import codecs,threading#流式 UTF-8 与串行操作
from ...内核.作用域 import 操作任务#操作链
from ...工具.惰性导入 import 创建惰性导入#xterm
from .输出跟随 import 终端跟随#跟随队列
from .类型 import 远程错误#控制权

__all__=['浏览器终端']#仅中文公开名

加载无头=创建惰性导入('@xterm/headless',__file__)#无头终端
加载序列化=创建惰性导入('@xterm/addon-serialize',__file__)#序列化

class 浏览器终端:#一路 PTY、有界仿真与可拆跟随者
    """进程寿命独立于跟随者与组件寿命。"""
    def __init__(自身,句柄,信息,回滚行,最大缓冲字节):#构造
        """记下句柄、初始元数据、回滚与每跟随者上限。"""
        自身.句柄=句柄#进程
        自身.info=信息#元数据 dict
        自身.最大缓冲字节=最大缓冲字节#上限
        无头=加载无头()#模块
        序列化模块=加载序列化()#模块
        终端类=无头.Terminal#类
        序列化类=序列化模块.SerializeAddon#类
        自身.屏幕=终端类({'cols':信息['cols'],'rows':信息['rows'],'scrollback':回滚行,'allowProposedApi':True})#仿真
        自身.序列化=序列化类()#插件
        自身.屏幕.loadAddon(自身.序列化)#装
        自身.跟随者=set()#跟随
        自身.序号=0#输出序号
        自身._操作=操作任务()#链
        自身._操作.兑现(None)#空链
        自身._关闭中=None#关闭任务
        自身._控制=None#当前可写附着
        自身._已排空=操作任务()#消费结束
        threading.Thread(target=自身._消费).start()#消费输出

    def 跟随(自身,标识,信号):#独占输入；旧附着只读
        """先交一致屏幕，再跟有序输出。"""
        若已中止则抛出本地(信号)#中止
        跟随者=终端跟随(自身.最大缓冲字节)#队列
        基线=自身._入队(lambda:自身._挂跟随(标识,跟随者,信号))#挂上
        try:#产出
            yield 基线#快照
            yield from 跟随者.读(信号)#后续
        finally:#摘
            自身.跟随者.discard(跟随者)#摘
            跟随者.关闭()#关
            if 自身._控制 is not None and 自身._控制['follower'] is 跟随者:#本控制
                自身._控制=None#放权
                信息=dict(自身.info)#拷
                信息.pop('controllerId',None)#去控制
                自身.info=信息#写回
                自身._广播({'type':'state','info':信息})#状态

    def _挂跟随(自身,标识,跟随者,信号):#在操作链上挂
        """登记控制者并交出快照。"""
        若已中止则抛出本地(信号)#中止
        自身._控制={'id':标识,'follower':跟随者}#控制
        信息=dict(自身.info)#拷
        信息['controllerId']=标识#控制者
        自身.info=信息#写回
        自身._广播({'type':'state','info':信息})#状态
        快照={'type':'snapshot','sequence':自身.序号,'screen':自身.序列化.serialize(),'info':信息}#快照
        自身.跟随者.add(跟随者)#登记
        return 快照#基线

    def 写入(自身,标识,数据):#原始输入
        """提供方接受后返回。"""
        def 操作():#链上
            """校验控制权后写。"""
            自身._要求控制(标识)#控制权
            自身.句柄.写入(数据)#写
        return 自身._入队(操作)#入队

    def 调整尺寸(自身,标识,列,行):#PTY 与恢复屏同一操作序
        """提供方与仿真都用新尺寸后返回。"""
        def 操作():#链上
            """校验、调远端、调仿真、广播。"""
            自身._要求控制(标识)#控制权
            自身.句柄.调整尺寸(列,行)#远端
            自身.屏幕.resize(列,行)#仿真
            信息=dict(自身.info)#拷
            信息['cols']=列#列
            信息['rows']=行#行
            自身.info=信息#写回
            自身._广播({'type':'state','info':信息})#状态
        return 自身._入队(操作)#入队

    def 重命名(自身,标题):#显示名
        """发给每个已附着视图。"""
        信息=dict(自身.info)#拷
        信息['title']=标题#标题
        自身.info=信息#写回
        自身._广播({'type':'state','info':信息})#状态

    def 关闭(自身):#先终止进程范围再放屏幕
        """失败可重试。"""
        if 自身._关闭中 is not None:#已开始
            自身._关闭中.等待()#等
            return#结束
        任务=操作任务()#本轮
        自身._关闭中=任务#记下
        def 跑():#线程
            """终止、排空、结束跟随、放屏幕。"""
            try:#关
                自身.句柄.终止()#终止
                自身._已排空.等待()#排空
                for 跟随者 in list(自身.跟随者):#跟随
                    跟随者.结束()#结束
                自身.跟随者.clear()#清空
                自身.屏幕.dispose()#放
                任务.兑现(None)#完
            except BaseException as 错误:#失败
                自身._关闭中=None#可重试
                任务.拒绝(错误)#唤醒等待
        threading.Thread(target=跑).start()#关
        任务.等待()#等

    def _要求控制(自身,标识):#可写附着
        """未运行或只读则 RemoteError。"""
        if 自身._关闭中 is not None or 自身.info['state']!='running':#未运行
            raise 远程错误('terminal/control-unavailable','Terminal is not running',{'reason':'not-running'})#拒绝
        if 自身._控制 is None or 自身._控制['id']!=标识:#他控
            raise 远程错误('terminal/control-unavailable','Terminal input is controlled by another attachment',{'reason':'read-only'})#只读

    def _广播(自身,帧):#所有跟随者
        """推入。"""
        for 跟随者 in list(自身.跟随者):#逐个
            跟随者.推入(帧)#推

    def _入队(自身,操作):#串行
        """调用方拥有失败；后续清理仍跑。"""
        上一=自身._操作#前
        当前=操作任务()#本
        自身._操作=当前#链
        def 跑():#线程
            """等前一个（忽略失败）再跑。"""
            try:#前
                上一.等待()#等
            except BaseException:#忽略
                pass#继续
            try:#本
                值=操作()#跑
                当前.兑现(值)#完
            except BaseException as 错误:#失败
                当前.拒绝(错误)#拒绝
        threading.Thread(target=跑).start()#跑
        return 当前.等待()#结果

    def _消费(自身):#读 PTY 输出
        """流式解码，EOF 后收退出事实。"""
        解码=codecs.getincrementaldecoder('utf-8')('replace')#忽略 BOM 由 utf-8 处理
        try:#消费
            for 块 in 自身.句柄.output:#逐块
                数据=解码.decode(块,True)#流式
                自身._输出(数据)#写屏
            自身._输出(解码.decode())#尾
            结局=自身.句柄.done.等待()#退出
            信息=dict(自身.info)#拷
            信息['state']='exited'#退出
            信息['exitCode']=结局['exitCode']#码
            自身.info=信息#写回
        except BaseException as 错误:#失败
            信息=dict(自身.info)#拷
            信息['state']='failed'#失败
            信息['error']=str(错误)#消息
            自身.info=信息#写回
        自身._广播({'type':'state','info':自身.info})#状态
        自身._已排空.兑现(None)#排空完

    def _输出(自身,数据):#写仿真并广播
        """空串跳过。"""
        if len(数据)==0:#空
            return#跳
        def 操作():#链上
            """写屏后广播 output。"""
            自身.屏幕.write(数据)#写
            自身.序号+=1#序号
            自身._广播({'type':'output','sequence':自身.序号,'data':数据})#输出
        自身._入队(操作)#入队

def 若已中止则抛出本地(信号):#本地中止
    """已中止则抛。"""
    if 信号 is None:#无
        return#放过
    if 信号.is_set():#已
        raise 远程错误('gateway/cancelled','aborted',{})#取消
