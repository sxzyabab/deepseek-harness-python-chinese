'Win32 对话框驱动的进程半边：拉起子进程，并转出关闭线程窗口'
import os,subprocess,sys,threading,json
from types import SimpleNamespace as 简单命名空间#工人对象
from .对话框绑定 import 关闭线程窗口#父进程关窗口

线程=threading.Thread#线程
锁=threading.Lock#锁
拉起进程=subprocess.Popen#子进程
解释器=sys.executable#解释器
环境变量=os.environ#环境
解码=json.loads#解码


def 拉起工作进程(数据):
    '拉起对话框子进程。标准输出一行一条 JSON，代替 Node 的 IPC'
    ################################
    #环境、引导，以及隐藏控制台
    ################################
    环境=dict(环境变量)#复制
    环境['DSH_DIALOG_TITLE']=数据['title']#标题
    环境['PYTHONIOENCODING']='utf-8'#消息通道按 utf-8
    模块名=__package__+'.对话框工作进程'#子进程模块
    语句='import sys\n'#引导
    语句=语句+'sys.path[:0]='+repr(list(sys.path))+'\n'#沿用父进程搜索路径
    语句=语句+'import runpy\n'#按模块执行
    语句=语句+'runpy.run_module('+repr(模块名)+',run_name="__main__")\n'#作为入口
    关键字={'stdin':subprocess.DEVNULL,'stdout':subprocess.PIPE,'stderr':None,'env':环境,'text':True,'encoding':'utf-8'}#标准流
    if os.name=='nt':#Windows
        关键字['creationflags']=subprocess.CREATE_NO_WINDOW#不弹控制台
    进程=拉起进程([解释器,'-c',语句],**关键字)#子进程
    ################################
    #message、error、exit
    ################################
    监听={'message':[],'error':[],'exit':[]}#监听表
    缓冲=[]#监听登记前到达的事件
    通道锁=锁()#读线程和登记串行

    def 派发(事件名,载荷):
        '把事件交给监听。还没有监听就先记下'
        with 通道锁:#和登记串行
            回调表=list(监听[事件名])#当前监听
            if len(回调表)==0:#还没有
                缓冲.append((事件名,载荷))#记下
                return#等登记
        for 回调 in 回调表:#逐个，不占着锁
            回调(载荷)#交给它

    def 订阅(事件名,监听函数):
        '登记 message、error 或 exit'
        with 通道锁:#和派发串行
            监听[事件名].append(监听函数)#记下
            留下=[]#其它事件
            待发=[]#这个事件的积压
            for 项 in 缓冲:#拆开积压
                if 项[0]==事件名:#属于这次登记
                    待发.append(项[1])#待发
                else:#其它
                    留下.append(项)#仍留下
            缓冲.clear()#清空
            for 项 in 留下:#放回
                缓冲.append(项)#其它事件
        for 载荷 in 待发:#补发，不占着锁
            监听函数(载荷)#交给新监听

    def 读循环():
        '按行读消息，管道结束后派发 exit'
        try:#读到关闭
            for 行 in 进程.stdout:#逐行
                派发('message',解码(行.strip()))#一条消息
        except Exception as 错误:#读失败
            派发('error',错误)#失败
        码=进程.wait()#等退出
        派发('exit',码)#退出

    def 杀掉():
        '强制结束子进程'
        进程.kill()#结束
        return True#已投递

    def 松开():
        '结算后不再把宿主退出拴在子进程上'
        return None#守护线程不拖住进程

    线程(target=读循环,daemon=True).start()#读线程
    return 简单命名空间(on=订阅,kill=杀掉,unref=松开)#工人
