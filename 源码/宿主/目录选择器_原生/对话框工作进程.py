'Win32 文件夹对话框子进程入口。阻塞在 Show 里，把 showing、done、error 写回父进程'
import json,os,sys,threading,traceback
from .对话框绑定 import 加载绑定#本机面
from .对话框逻辑 import 运行文件夹对话框#COM 顺序
from .异常 import 目录选择器原生错误#失败

编码=json.dumps#编码
父进程号=os.getppid#父进程号
立即退出=os._exit#立即结束
环境变量=os.environ#环境
线程=threading.Thread#线程
事件=threading.Event#等待
缺标题='win32-dialog-worker: DSH_DIALOG_TITLE is required'#没有标题
缺通道='win32-dialog-worker must run as a child process with an IPC channel'#不是子进程通道
父进程轮询秒=0.2#代替 Node 的 disconnect


def 发送(消息):
    '写一行 JSON。父进程按行读，写完就flush，Show 阻塞期间父进程也能读到'
    sys.stdout.write(编码(消息,ensure_ascii=False)+'\n')#一行
    sys.stdout.flush()#立刻送出


def 监视父进程():
    '父进程退出则结束，避免对话框留在屏幕上'
    父=父进程号()#启动时的父进程
    等待=事件()#只用来睡觉
    while True:#轮询
        if 父进程号()!=父:#父已换
            立即退出(0)#结束
        等待.wait(父进程轮询秒)#间隔


if __name__=='__main__':#只在被拉起时跑。包导入不打开对话框
    标题=环境变量.get('DSH_DIALOG_TITLE','')#标题
    if 标题=='':#缺标题
        raise 目录选择器原生错误(缺标题)#拒绝
    输出=sys.stdout#消息通道
    if 输出 is None or 输出.isatty():#没有管道
        raise 目录选择器原生错误(缺通道)#拒绝
    线程(target=监视父进程,daemon=True).start()#父进程断开就退出
    try:#跑对话框
        def 显示中(线程号):
            'Show 之前把线程号交给驱动'
            发送({'kind':'showing','threadId':线程号})#通知
        路径=运行文件夹对话框(加载绑定(),标题,显示中)#阻塞
        发送({'kind':'done','path':路径})#结果
    except Exception as 错误:#失败
        说明=''.join(traceback.format_exception(type(错误),错误,错误.__traceback__))#栈
        发送({'kind':'error','message':说明})#错误
