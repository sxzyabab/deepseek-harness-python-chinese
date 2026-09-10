"""`ctx.resources`：协议提供方登记表与按地址状态，支撑使用资源。

对齐上游 `resources/src/client/resources.ts`。
每条地址一条记录，页面存续期内不丢弃；末位持有者释放时只中止流并把快照重置为空闲。
AbortSignal 译为 threading.Event；提供方 open 的帧流译为同步可迭代，在守护线程中消费。
"""
import json#登记诊断标签
import threading#中止旗与消费线程
from urllib.parse import urlparse#解析资源地址
from .约定 import (#状态字面量与服务约定
    资源状态_无,
    资源状态_加载中,
    资源状态_存活,
    资源状态_失败,
    资源服务协议,
)#约定导入结束

__all__=[#仅中文公开名
    '资源方案',
    '取协议',
    '资源错误',
    '已中止',
    '若已中止则抛出',
    '资源注册表',
]#公开面结束

资源方案='dsh-resource'#资源地址 scheme，无冒号

class 资源错误(Exception):
    """本包资源模型失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 已中止(信号):#读 threading.Event
    """无信号视为未中止。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#置位即中止

def 若已中止则抛出(信号):#已取消则抛
    """已中止则抛资源错误。"""
    if 已中止(信号):#已取消
        raise 资源错误('The operation was aborted.')#中止

def 取协议(地址):#读资源地址的协议键
    """`dsh-resource://` 的 host（小写）；其它字符串视为无协议。"""
    try:#URL 解析
        解析=urlparse(地址)#解析
    except ValueError:#非法
        return None#非资源地址
    if 解析.scheme!=资源方案:#其它 scheme
        return None#非资源地址
    主机=解析.hostname#host
    if 主机 is None or 主机=='':#无 host
        return None#非资源地址
    return 主机.lower()#协议键小写

def 空闲快照(状态):#空闲态快照
    """无值、无失败。"""
    return {'status':状态,'value':None,'failure':None}#空闲

class 快照存储:#本包自持的快照存储
    """getSnapshot / subscribe / set；对齐 createSnapshotStore 的同步面。"""
    def __init__(自身,初值):#初值
        """记下状态。"""
        自身._状态=初值#当前快照
        自身._监听=set()#订阅者

    def getSnapshot(自身):#读
        """返回当前快照引用。"""
        return 自身._状态#快照

    def subscribe(自身,监听器):#订阅
        """返回拆除器。"""
        自身._监听.add(监听器)#登记
        def 拆除():#退订
            """从集删除。"""
            自身._监听.discard(监听器)#删
        return 拆除#拆除器

    def set(自身,下一):#整表替换
        """写快照并广播。"""
        自身._状态=下一#替换
        for 监听 in list(自身._监听):#复制后派发
            try:#单回调
                监听()#通知
            except Exception as 错误:#不得饿死其余
                print('[client-resources] subscriber failed:',错误)#诊断

class 资源记录:#一地址的运行态
    """快照、持有者计数与运行中流的中止旗。"""
    def __init__(自身,地址,协议,存储,源):#组装
        """记下不可变字段与可变计数。"""
        自身.地址=地址#完整地址
        自身.协议=协议#协议键或 None
        自身.存储=存储#快照存储
        自身.源=源#可观察源
        自身.持有者数=0#订阅者加钉住
        自身.控制器=None#运行中流的 Event

class 资源源:#可观察快照面
    """getSnapshot 不持有；subscribe 增减持有者。"""
    def __init__(自身,取快照,订阅):#绑定闭包
        """登记取快照与订阅。"""
        自身.getSnapshot=取快照#当前快照
        自身.subscribe=订阅#订阅，返回取消函数

class 资源注册表(资源服务协议):#ctx.resources 实现
    """提供方登记表与按地址记录。"""
    def __init__(自身,上下文):#构造
        """记下登记效应所属上下文。"""
        自身._上下文=上下文#Cordis 上下文
        自身._提供方={}#协议 → 提供方 dict
        自身._记录={}#地址 → 资源记录

    def 登记(自身,提供方):#登记一协议
        """一协议恰有一个提供方（dict：protocol/open）；返回幂等拆除器。"""
        协议=提供方['protocol']#协议键
        if 协议 in 自身._提供方:#已有
            raise 资源错误('resources: protocol "'+str(协议)+'" already has a provider')#拒绝二次
        def 寿命():#提供方生命周期
            """挂上后对已持有地址开流。"""
            自身._提供方[协议]=提供方#写入
            for 记录 in 自身._协议下记录(协议):#该协议地址
                自身._挂上(记录)#持有则开流，空闲则 loading
            def 拆除():#提供方离开
                """结束流并报 none。"""
                自身._提供方.pop(协议,None)#删除
                for 记录 in 自身._协议下记录(协议):#该协议地址
                    自身._卸下(记录)#停流并 none
            return 拆除#拆除器
        拆除=自身._上下文.副作用(寿命,'resources.register('+json.dumps(协议,ensure_ascii=False)+')')#登记效应
        def 对外拆除():#幂等对外
            """拆除登记。"""
            拆除()#卸
        return 对外拆除#对外 disposer

    def 钉住(自身,地址,信号):#不订阅地持有
        """信号中止前保持打开；已中止则钉不住。"""
        if 已中止(信号):#已中止
            return#空操作
        记录=自身._取记录(地址)#取或建
        自身._持有(记录)#加持有者
        def 监视中止():#等信号置位
            """中止后释放。"""
            信号.wait()#阻塞至 abort
            自身._释放(记录)#释放钉住
        线=threading.Thread(target=监视中止,daemon=True,name='dsh-resource-pin')#守护线程
        线.start()#启动

    def 取源(自身,地址):#活源
        """一地址一条，引用稳定。"""
        return 自身._取记录(地址).源#可观察源

    def _取记录(自身,地址):#取或建记录
        """页面存续期内保留。"""
        记录=自身._记录[地址] if 地址 in 自身._记录 else None#已有
        if 记录 is None:#新建
            记录=自身._创建(地址)#创建
            自身._记录[地址]=记录#挂上
        return 记录#记录

    def _创建(自身,地址):#新建记录
        """初态按是否有提供方取 none 或 loading。"""
        协议=取协议(地址)#协议键
        初态=资源状态_无 if 自身._取提供方(协议) is None else 资源状态_加载中#初态
        存储=快照存储(空闲快照(初态))#快照存储
        记录盒={'v':None}#创建后回填，供闭包持有同一记录

        def 取快照():#读存储
            """不持有。"""
            return 存储.getSnapshot()#当前

        def 订阅(监听器):#订阅并持有
            """退订时释放。"""
            退订存储=存储.subscribe(监听器)#存储订阅
            自身._持有(记录盒['v'])#加持有者
            活跃=[True]#幂等门闩
            def 取消():#退订
                """只生效一次。"""
                if not 活跃[0]:#已退
                    return#停
                活跃[0]=False#标记
                退订存储()#卸存储监听
                自身._释放(记录盒['v'])#释放持有
            return 取消#取消器

        源=资源源(取快照,订阅)#可观察源
        记录=资源记录(地址,协议,存储,源)#组装
        记录盒['v']=记录#回填
        return 记录#记录

    def _取提供方(自身,协议):#按协议取提供方
        """无协议则无。"""
        if 协议 is None:#非资源地址
            return None#无
        return 自身._提供方[协议] if 协议 in 自身._提供方 else None#提供方

    def _协议下记录(自身,协议):#该协议全部记录
        """生成器。"""
        for 记录 in 自身._记录.values():#全部
            if 记录.协议==协议:#匹配
                yield 记录#交出

    def _持有(自身,记录):#加持有者
        """首位打开流。"""
        记录.持有者数+=1#加一
        if 记录.持有者数==1:#首位
            自身._启动(记录)#开流

    def _释放(自身,记录):#减持有者
        """末位中止流并重置空闲。"""
        记录.持有者数-=1#减一
        if 记录.持有者数>0:#仍有持有者
            return#共享流
        自身._停止(记录)#中止
        空闲=资源状态_无 if 自身._取提供方(记录.协议) is None else 资源状态_加载中#空闲态
        记录.存储.set(空闲快照(空闲))#重置

    def _挂上(自身,记录):#提供方到达
        """持有则开流，空闲则 loading。"""
        if 记录.持有者数>0:#已持有
            自身._启动(记录)#开流
            return#结束
        记录.存储.set(空闲快照(资源状态_加载中))#转 loading

    def _卸下(自身,记录):#提供方离开
        """停流并报 none。"""
        自身._停止(记录)#中止
        记录.存储.set(空闲快照(资源状态_无))#none

    def _启动(自身,记录):#打开提供方流
        """无提供方则跳过。"""
        方=自身._取提供方(记录.协议)#提供方
        if 方 is None:#无
            return#跳过
        控制器=threading.Event()#本流中止旗
        记录.控制器=控制器#挂上
        if 记录.存储.getSnapshot()['status']!=资源状态_加载中:#非 loading
            记录.存储.set(空闲快照(资源状态_加载中))#先 loading
        线=threading.Thread(#守护消费线程
            target=自身._消费,
            args=(记录,方,控制器),
            daemon=True,
            name='dsh-resource-consume',
        )#结束 Thread
        线.start()#启动

    def _停止(自身,记录):#中止运行中流
        """置位并摘掉控制器。"""
        if 记录.控制器 is not None:#有流
            记录.控制器.set()#abort
            记录.控制器=None#摘掉

    def _消费(自身,记录,提供方,信号):#消费帧流
        """失败以帧表达；流内抛错不捕获。"""
        流=提供方['open'](记录.地址,{'signal':信号})#开流
        for 帧 in 流:#逐帧
            if 已中止(信号):#释放后到达的帧丢弃
                break#结束并归还迭代器
            if 帧['ok']:#成功帧
                记录.存储.set({#存活
                    'status':资源状态_存活,
                    'value':帧['value'],
                    'failure':None,
                })#结束 set
            else:#失败帧
                记录.存储.set({#失败，保留末值
                    'status':资源状态_失败,
                    'value':记录.存储.getSnapshot()['value'],
                    'failure':帧['error'],
                })#结束 set
