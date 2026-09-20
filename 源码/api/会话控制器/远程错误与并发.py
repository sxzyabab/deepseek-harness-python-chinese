"""会话控制器远程错误、中止查询与线程任务。"""
import threading#后台任务
from threading import Event as 同步事件#跨线程结算广播

__all__=['远程错误','远程错误消息','已中止','若已中止则抛出','在线程执行']#仅中文公开名

class 远程错误(Exception):
    """远程错误。附加信息做成属性。"""
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

def 在线程执行(函数):
    """在工作线程执行；返回仅含 等待结局 的句柄。回调翻译时已是同步函数。"""
    完成=同步事件()#结算广播
    箱={'结果':None,'错误':None}#结算字段
    def 执行并结算():
        """执行函数并写入结算字段。"""
        try:
            箱['结果']=函数()#同步返回值
        except BaseException as 错误:
            箱['错误']=错误#原样记下
        finally:
            完成.set()#广播
    工作=threading.Thread(target=执行并结算)#工作线程
    工作.daemon=True#不挡住退出
    工作.start()
    class 线程结局:
        """跨线程工作结局；只公开 等待结局。"""
        def 等待结局(自身):
            """阻塞到工作结束；失败原样抛。"""
            完成.wait()#等结算
            if 箱['错误'] is not None:
                raise 箱['错误']#原样抛
            return 箱['结果']#成功值
    return 线程结局()#句柄
