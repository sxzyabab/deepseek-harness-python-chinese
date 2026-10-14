'Win32 文件夹对话框子进程入口。管道上每行一条 JSON，对应宿主 IPC'
import json,os,re,sys,importlib.util,threading,time,traceback#协议、环境、父进程与同目录加载

_绝对路径=re.compile(
    r'[A-Za-z]:[\\/][^\s\'"]+|\\\\[^\s\'"]+|/(?:[^/\s\'"]+)+(?:/[^/\s\'"]+)*'
)#盘符、UNC、POSIX 绝对

def 去绝对路径(文本):#异常说明
    '说明里不保留绝对路径'
    return _绝对路径.sub('',文本).replace('""','').replace("''",'')#去掉路径

def 异常说明(错误):#带回栈，但不带绝对路径
    '子进程失败时写给父进程的说明'
    文本=''.join(traceback.format_exception(type(错误),错误,错误.__traceback__))#栈
    文本=去绝对路径(文本).strip()#去路径
    if 文本!='':#还有字
        return 文本#说明
    return 去绝对路径(str(错误)).strip()#退回消息

def 有消息通道():#stdout 管道充当 IPC
    '控制台直连不算通道'
    输出=sys.stdout#标准输出
    if 输出 is None:#没有
        return False#无通道
    try:#isatty
        return not 输出.isatty()#管道或文件
    except OSError:#已关
        return True#仍当通道

def 监视父进程():#父进程退出则结束
    '避免父进程断开后对话框还留在屏幕上'
    父=os.getppid()#启动时的父进程
    while True:#轮询
        if os.getppid()!=父:#父已换
            os._exit(0)#结束
        time.sleep(0.2)#间隔

def 同目录(名):#按文件名加载同目录模块
    '子进程以脚本运行时没有包上下文'
    路径=os.path.join(os.path.dirname(os.path.abspath(__file__)),名+'.py')#文件
    规格=importlib.util.spec_from_file_location(名,路径)#规格
    模块=importlib.util.module_from_spec(规格)#空模块
    规格.loader.exec_module(模块)#执行
    return 模块#模块

def 发送(消息):#写一行 JSON
    '父进程按行读'
    sys.stdout.write(json.dumps(消息,ensure_ascii=False)+'\n')#一行
    sys.stdout.flush()#立刻送出

def 主():#阻塞在 Show 里，结果写回消息通道
    '标题来自 DSH_DIALOG_TITLE；没有管道则拒绝'
    标题=os.environ.get('DSH_DIALOG_TITLE','')#标题
    if 标题=='':#缺标题
        raise SystemExit('win32-dialog-worker: DSH_DIALOG_TITLE is required')#拒绝
    if not 有消息通道():#没有管道
        raise SystemExit('win32-dialog-worker must run as a child process with an IPC channel')#拒绝
    threading.Thread(target=监视父进程,daemon=True).start()#父进程断开就退出
    逻辑=同目录('对话框逻辑')#顺序
    绑定=同目录('对话框绑定')#本机面
    try:#跑对话框
        def 显示中(线程号):#Show 之前
            '把线程号交给驱动'
            发送({'kind':'showing','threadId':线程号})#通知
        路径=逻辑.运行文件夹对话框(绑定.加载绑定(),标题,显示中)#阻塞
        发送({'kind':'done','path':路径})#结果
    except Exception as 错误:#失败
        发送({'kind':'error','message':异常说明(错误)})#错误，不含绝对路径

if __name__=='__main__':#作为子进程启动
    主()#跑
