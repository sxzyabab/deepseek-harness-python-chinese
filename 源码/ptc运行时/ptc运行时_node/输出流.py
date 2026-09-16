"""受管执行结束后，对原始进程输出做有界排空。"""
import threading#宽限等待
from .协议 import 节点ptc错误#本包异常

__all__=['排空输出']#仅中文公开名

def 排空输出(流,宽限毫秒):#等到排队字节排完或宽限到期
    """等待已排队字节，不让继承描述符把一次运行永远卡住。流是调用方拥有的原始进程输出。宽限毫秒是受管终止后的最长等待。返回完整流是否无传输错误地结束。"""
    if 流 is None:#未提供
        return True#视为干净结束
    已关=getattr(流,'closed',False)#是否已关
    if 已关:#已关闭
        return False#传输未干净结束
    完成=threading.Event()#排空完成
    干净=[True]#默认干净
    def 读尽():#读到 EOF
        """读到结束或出错。"""
        try:#读管道
            while True:#直到 EOF
                块=流.read(65536)#一块
                if not 块:#结束
                    break#停
        except (OSError,ValueError,节点ptc错误):#传输错误
            干净[0]=False#不干净
        完成.set()#完成
    线程=threading.Thread(target=读尽,daemon=True)#后台排空
    线程.start()#开始
    if not 完成.wait(宽限毫秒/1000.0):#宽限内未结束
        return False#超时
    return 干净[0]#是否干净
