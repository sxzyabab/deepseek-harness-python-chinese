'Win32 文件夹对话框驱动：子进程里阻塞 Show，中止时给那个线程的窗口投 WM_CLOSE'
import json,os,subprocess,sys,threading#子进程与中止
对话框标题='Select Workspace Directory'#每个宿主用的标题
关闭间隔秒=0.15#重投间隔
关闭最多=20#超过则杀掉子进程

def 选Win32目录(信号,内部=None):#打开现代文件夹选择框
    '返回选中路径；取消返回 None；中止抛错'
    if 内部 is None:#无测试钩子
        内部={}#空
    if 已中止(信号):#调用前已取消
        raise OSError('native directory picker aborted')#中止
    拉起=内部['spawnWorker'] if 'spawnWorker' in 内部 else 拉起工作进程#子进程
    if 'closeThreadWindows' in 内部:#测试钩子
        关闭=内部['closeThreadWindows']#替换
    else:#生产
        from .对话框绑定 import 关闭线程窗口#只在 Windows 上加载
        关闭=关闭线程窗口#关窗口
    间隔=内部['closeRetryMs']/1000 if 'closeRetryMs' in 内部 else 关闭间隔秒#间隔秒
    工人=拉起({'title':对话框标题})#子进程
    线程号={'值':None}#showing 之后才有
    已结算=threading.Event()#只结算一次
    结果箱={'值':None,'错误':None}#结果

    def 结算(成功,值):#第一次生效
        '停掉中止服务并记下结果'
        if 已结算.is_set():#已经结算
            return#忽略
        已结算.set()#占住
        if 成功:#路径或 None
            结果箱['值']=值#记下
        else:#失败
            结果箱['错误']=值#记下

    def 投关闭():#有线程号才投
        '关窗口失败就等下一次'
        if 线程号['值'] is None:#还没有窗口
            return#等
        try:#投递
            关闭(线程号['值'])#WM_CLOSE
        except Exception:#拒绝也继续重试
            return#丢掉

    def 服务中止():#中止后重投，最后杀进程
        '预算用完就杀掉子进程'
        次数=0#已尝试
        投关闭()#立刻一次
        while not 已结算.wait(间隔):#间隔
            次数+=1#加一
            if 次数>关闭最多:#预算用完
                try:#最后手段
                    工人.kill()#杀
                except Exception:#已经没了
                    pass#忽略
                结算(False,OSError('native directory picker aborted (dialog unresponsive; worker killed)'))#失败
                return#停
            投关闭()#再投

    def 等中止():#信号置位后开始服务
        '无信号则不中止'
        if 信号 is None:#无信号
            return#不服务
        信号.wait()#阻塞到置位
        if not 已结算.is_set():#还在选
            服务中止()#开始关

    threading.Thread(target=等中止,daemon=True).start()#中止线程

    def 读():#读子进程 stdout
        '一行一条消息'
        try:#读到管道关
            for 行 in 工人.stdout:#逐行
                消息=json.loads(行)#协议
                种类=消息['kind']#种类
                if 种类=='showing':#窗口出来了
                    线程号['值']=消息['threadId']#记下
                    if 已中止(信号):#中止抢先到了
                        投关闭()#现在有窗口可关
                elif 种类=='done':#选完
                    if 已中止(信号):#中止优先
                        结算(False,OSError('native directory picker aborted'))#中止
                    else:#正常
                        结算(True,消息['path'])#路径或 None
                    return#停读
                elif 种类=='error':#子进程失败
                    结算(False,OSError('win32 folder dialog failed: '+消息['message']))#失败
                    return#停读
                else:#未知
                    结算(False,TypeError('unknown win32 dialog worker message kind: '+str(种类)))#失败
                    return#停读
        except Exception as 错误:#读失败
            结算(False,错误)#失败
            return#停
        结算(False,OSError('win32 folder dialog worker exited before reporting a result'))#没报告就退出

    读线程=threading.Thread(target=读,daemon=True)#读线程
    读线程.start()#开始
    读线程.join()#等到结算
    if 结果箱['错误'] is not None:#失败
        raise 结果箱['错误']#抛
    return 结果箱['值']#路径或 None

def 拉起工作进程(数据):#拉起对话框子进程
    'stdout 是消息通道'
    环境=dict(os.environ)#复制
    环境['DSH_DIALOG_TITLE']=数据['title']#标题
    关键字={'stdout':subprocess.PIPE,'stderr':None,'stdin':subprocess.DEVNULL,'text':True,'encoding':'utf-8'}#管道
    if os.name=='nt':#Windows
        关键字['creationflags']=subprocess.CREATE_NO_WINDOW#不弹控制台
    脚本=os.path.join(os.path.dirname(os.path.abspath(__file__)),'对话框工作进程.py')#子进程脚本
    return subprocess.Popen([sys.executable,脚本],env=环境,**关键字)#子进程
