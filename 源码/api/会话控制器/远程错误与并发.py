"""会话控制器远程错误、中止查询与线程任务。

对齐上游会话控制器杂物袋：RemoteError、Abort 查询与工作线程任务。公开面仅中文名。
"""
import threading#后台任务
from concurrent.futures import Future as 原生结果#单次操作结果

__all__=['远程错误','远程错误消息','已中止','若已中止则抛出','操作任务','在线程执行']#仅中文公开名

class 远程错误(Exception):
    """对齐上游 RemoteError。附加信息做成属性。"""
    def __init__(自身,码,消息,详情=None,原因=None):
        """记下 code/message/details。"""
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details={} if 详情 is None else 详情#详情
        if 原因 is not None:#原因
            自身.__cause__=原因#链接

def 远程错误消息(错误):
    """把错误收成字符串。"""
    return str(错误)#消息

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号为 threading.Event。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位

def 若已中止则抛出(信号):
    """已中止则抛出取消。"""
    if 已中止(信号):#已中止
        raise 远程错误('gateway/cancelled','aborted',{})#取消

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                包装=远程错误('gateway/internal','task rejected',{})#包装拒绝
                包装.原因=错误#附加属性
                自身._未来.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

def 在线程执行(函数):
    """在工作线程执行并返回任务。回调翻译时已是同步函数。"""
    任务=操作任务()#本次任务
    def 执行并结算():
        """执行函数并结算。"""
        try:
            任务.兑现(函数())#兑现同步返回值
        except BaseException as 错误:
            任务.拒绝(错误)#拒绝
    工作=threading.Thread(target=执行并结算)#工作线程
    工作.daemon=True#不挡住退出
    工作.start()#启动
    return 任务#操作任务
