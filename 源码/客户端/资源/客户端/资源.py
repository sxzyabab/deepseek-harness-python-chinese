import json#登记诊断标签
import threading#中止标志与消费线程
from urllib.parse import urlparse as 解析URL
from .约定 import (
    资源状态_无,
    资源状态_加载中,
    资源状态_存活,
    资源状态_失败,
    资源服务协议,
)

__all__=[
    '资源方案',
    '取协议',
    '资源错误',
    '已中止',
    '若已中止则抛出',
    '资源注册表',
]

资源方案='dsh-resource'#资源地址 scheme，无冒号

class 资源错误(Exception):
    """本包资源模型失败。"""
    def __init__(自身,消息):
        """记下消息；线协议比对用的英文原样保留。"""
        super().__init__(消息)

def 已中止(信号):
    """无信号视为未中止；信号为 threading.Event。"""
    if 信号 is None:
        return False
    return 信号.is_set()

def 若已中止则抛出(信号):
    """已中止则抛资源错误。"""
    if 已中止(信号):
        raise 资源错误('The operation was aborted.')#线协议英文

def 取协议(地址):
    """dsh-resource:// 的 host（小写）；其它字符串视为无协议。"""
    try:
        解析=解析URL(地址)
    except ValueError:
        return None
    if 解析.scheme!=资源方案:
        return None
    主机=解析.hostname
    if 主机 is None or 主机=='':
        return None
    return 主机.lower()

def 空闲快照(状态):
    """无值、无失败的空闲态快照。"""
    return {'status':状态,'value':None,'failure':None}

class 快照存储:
    """本包自持的同步快照存储：getSnapshot / subscribe / set。"""
    def __init__(自身,初值):
        """记下初始快照。"""
        自身._状态=初值
        自身._监听=set()

    def getSnapshot(自身):
        """返回当前快照引用。"""
        return 自身._状态

    def subscribe(自身,监听器):
        """登记监听器，返回拆除器。"""
        自身._监听.add(监听器)
        def 拆除():
            """从订阅集删除。"""
            自身._监听.discard(监听器)
        return 拆除

    def set(自身,下一):
        """写快照并广播；单回调失败不得饿死其余监听器。"""
        自身._状态=下一
        for 监听 in list(自身._监听):
            try:
                监听()
            except Exception as 错误:
                print('[client-resources] 订阅者失败:',错误)

class 资源记录:
    """一地址的运行态：快照、持有者计数与运行中流的中止旗。"""
    def __init__(自身,地址,协议,存储,源):
        """记下不可变字段与可变计数。"""
        自身.地址=地址
        自身.协议=协议
        自身.存储=存储
        自身.源=源
        自身.持有者数=0#订阅者加钉住
        自身.控制器=None#运行中流的 Event

class 资源源:
    """可观察快照面：getSnapshot 不持有；subscribe 增减持有者。"""
    def __init__(自身,取快照,订阅):
        """登记取快照与订阅闭包。"""
        自身.getSnapshot=取快照
        自身.subscribe=订阅

class 资源注册表(资源服务协议):
    """resources 服务实现：提供方登记表与按地址记录。"""
    def __init__(自身,上下文):
        """记下登记效应所属上下文。"""
        自身._上下文=上下文
        自身._提供方={}#协议 → 提供方 dict
        自身._记录={}#地址 → 资源记录

    def 登记(自身,提供方):
        """一协议恰有一个提供方（dict：protocol/open）；返回幂等拆除器。"""
        协议=提供方['protocol']
        if 协议 in 自身._提供方:
            raise 资源错误('resources: protocol "'+str(协议)+'" already has a provider')
        def 寿命():
            """挂上后对已持有地址开流。"""
            自身._提供方[协议]=提供方
            for 记录 in 自身._协议下记录(协议):
                自身._挂上(记录)#持有则开流，空闲则 loading
            def 拆除():
                """结束流并报 none。"""
                自身._提供方.pop(协议,None)
                for 记录 in 自身._协议下记录(协议):
                    自身._卸下(记录)
            return 拆除
        拆除=自身._上下文.副作用(寿命,'resources.register('+json.dumps(协议,ensure_ascii=False)+')')
        def 对外拆除():
            """拆除登记。"""
            拆除()
        return 对外拆除

    def 钉住(自身,地址,信号):
        """信号中止前保持打开；已中止则钉不住。"""
        if 已中止(信号):
            return
        记录=自身._取记录(地址)
        自身._持有(记录)
        def 监视中止():
            """中止后释放钉住。"""
            信号.wait()
            自身._释放(记录)
        线=threading.Thread(target=监视中止,daemon=True,name='dsh-resource-pin')
        线.start()

    def 取源(自身,地址):
        """一地址一条活源，引用稳定。"""
        return 自身._取记录(地址).源

    def _取记录(自身,地址):
        """页面存续期内保留记录。"""
        记录=自身._记录[地址] if 地址 in 自身._记录 else None
        if 记录 is None:
            记录=自身._创建(地址)
            自身._记录[地址]=记录
        return 记录

    def _创建(自身,地址):
        """初态按是否有提供方取 none 或 loading。"""
        协议=取协议(地址)
        初态=资源状态_无 if 自身._取提供方(协议) is None else 资源状态_加载中
        存储=快照存储(空闲快照(初态))
        记录盒={'v':None}#创建后回填，供闭包持有同一记录

        def 取快照():
            """读存储，不持有。"""
            return 存储.getSnapshot()

        def 订阅(监听器):
            """订阅并持有；退订时释放。"""
            退订存储=存储.subscribe(监听器)
            自身._持有(记录盒['v'])
            活跃=[True]#幂等门闩
            def 取消():
                """只生效一次。"""
                if not 活跃[0]:
                    return
                活跃[0]=False
                退订存储()
                自身._释放(记录盒['v'])
            return 取消

        源=资源源(取快照,订阅)
        记录=资源记录(地址,协议,存储,源)
        记录盒['v']=记录
        return 记录

    def _取提供方(自身,协议):
        """无协议则无提供方。"""
        if 协议 is None:
            return None
        return 自身._提供方[协议] if 协议 in 自身._提供方 else None

    def _协议下记录(自身,协议):
        """生成该协议下全部记录。"""
        for 记录 in 自身._记录.values():
            if 记录.协议==协议:
                yield 记录

    def _持有(自身,记录):
        """加持有者；首位打开流。"""
        记录.持有者数+=1
        if 记录.持有者数==1:
            自身._启动(记录)

    def _释放(自身,记录):
        """减持有者；末位中止流并重置空闲。"""
        记录.持有者数-=1
        if 记录.持有者数>0:
            return
        自身._停止(记录)
        空闲=资源状态_无 if 自身._取提供方(记录.协议) is None else 资源状态_加载中
        记录.存储.set(空闲快照(空闲))

    def _挂上(自身,记录):
        """提供方到达：持有则开流，空闲则 loading。"""
        if 记录.持有者数>0:
            自身._启动(记录)
            return
        记录.存储.set(空闲快照(资源状态_加载中))

    def _卸下(自身,记录):
        """提供方离开：停流并报 none。"""
        自身._停止(记录)
        记录.存储.set(空闲快照(资源状态_无))

    def _启动(自身,记录):
        """打开提供方流；无提供方则跳过。"""
        方=自身._取提供方(记录.协议)
        if 方 is None:
            return
        控制器=threading.Event()
        记录.控制器=控制器
        if 记录.存储.getSnapshot()['status']!=资源状态_加载中:
            记录.存储.set(空闲快照(资源状态_加载中))
        线=threading.Thread(
            target=自身._消费,
            args=(记录,方,控制器),
            daemon=True,
            name='dsh-resource-consume',
        )
        线.start()

    def _停止(自身,记录):
        """置位中止旗并摘掉控制器。"""
        if 记录.控制器 is not None:
            记录.控制器.set()
            记录.控制器=None

    def _消费(自身,记录,提供方,信号):
        """失败以帧表达；流内抛错不捕获。释放后到达的帧丢弃。"""
        流=提供方['open'](记录.地址,{'signal':信号})
        for 帧 in 流:
            if 已中止(信号):
                break
            if 帧['ok']:
                记录.存储.set({
                    'status':资源状态_存活,
                    'value':帧['value'],
                    'failure':None,
                })
            else:#失败帧保留末值
                记录.存储.set({
                    'status':资源状态_失败,
                    'value':记录.存储.getSnapshot()['value'],
                    'failure':帧['error'],
                })
