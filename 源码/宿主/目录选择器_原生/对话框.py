'Win32 文件夹对话框驱动：子进程里阻塞 Show，中止时给那个线程的窗口投 WM_CLOSE'
import threading
from ...工具.原生命令 import 已中止#调用方寿命
from .对话框宿主 import 拉起工作进程,关闭线程窗口#子进程与关窗口
from .异常 import 目录选择器原生错误,选择已中止#失败

线程=threading.Thread#线程
事件=threading.Event#事件
锁=threading.Lock#锁
对话框标题='Select Workspace Directory'#每个宿主用的标题
关闭间隔毫秒=150#重投间隔
关闭最多=20#超过则杀掉子进程
中止轮询秒=0.05#等到结算或信号
无回应文案='native directory picker aborted (dialog unresponsive; worker killed)'#预算用完
提前退出文案='win32 folder dialog worker exited before reporting a result'#没报告就退出
失败前缀='win32 folder dialog failed: '#子进程失败
未知种类前缀='unknown win32 dialog worker message kind: '#封闭并集兜底


def 选Win32目录(信号,内部=None):
    '返回选中路径；取消返回 None。中止抛错'
    ################################
    #钩子、间隔，以及调用前已经中止
    ################################
    if 内部 is None:#无测试钩子
        内部={}#空表
    if 已中止(信号):#调用前已取消
        raise 选择已中止()#中止
    if 内部.get('spawnWorker') is not None:#测试替换子进程
        拉起=内部['spawnWorker']#替换
    else:#生产子进程
        拉起=拉起工作进程#子进程
    if 内部.get('closeThreadWindows') is not None:#测试替换关窗口
        关闭=内部['closeThreadWindows']#替换
    else:#生产关窗口
        关闭=关闭线程窗口#关窗口
    if 内部.get('closeRetryMs') is not None:#测试间隔
        间隔毫秒=内部['closeRetryMs']#毫秒
    else:#生产间隔
        间隔毫秒=关闭间隔毫秒#毫秒
    间隔秒=间隔毫秒/1000#秒
    工人=拉起({'title':对话框标题})#子进程
    状态={'线程号':None,'已结算':False,'定时':None,'结果':None,'错误':None}#一次选择
    互斥=锁()#结算只发生一次
    完成=事件()#调用方在这里等

    def 结算(动作):
        '只结算一次，停掉中止服务，再执行结果'
        with 互斥:#串行
            if 状态['已结算']:#已经结算
                return#忽略
            状态['已结算']=True#占住
            定时=状态['定时']#中止循环
            if 定时 is not None:#已经在关
                定时.set()#叫醒它
            try:#松开并交出结果
                松开=getattr(工人,'unref',None)#可选
                if 松开 is not None:#有
                    松开()#不再拖住宿主退出
                动作()#记下路径或错误
            except Exception as 错误:#结果动作自己失败
                if 状态['错误'] is None:#还没有失败
                    状态['错误']=错误#记下
            finally:#无论如何叫醒调用方
                完成.set()#结束等待

    def 投关闭():
        '有线程号才投 WM_CLOSE。投递失败丢掉，下一轮再试'
        if 状态['线程号'] is None:#还没有窗口
            return#等 showing
        try:#投递
            关闭(状态['线程号'])#WM_CLOSE
        except Exception as 关闭失败:#EnumThreadWindows 或 PostMessageW 拒绝
            return#丢掉，间隔会再投

    def 当消息(消息):
        '处理子进程回传的 showing、done、error'
        种类=消息['kind']#协议种类
        if 种类=='showing':#窗口即将显示
            状态['线程号']=消息['threadId']#记下线程
            if 已中止(信号):#中止抢在通知之前
                投关闭()#现在有窗口
            return#继续等结果
        if 种类=='done':#人选完或取消
            def 记下():
                '中止优先于路径'
                if 已中止(信号):#已经中止
                    状态['错误']=选择已中止()#中止
                    return#不再记路径
                状态['结果']=消息['path']#路径或 None
            结算(记下)#结算
            return#结束
        if 种类=='error':#子进程失败
            def 记下():
                '把子进程说明原样交给调用方'
                状态['错误']=目录选择器原生错误(失败前缀+消息['message'])#失败
            结算(记下)#结算
            return#结束
        def 记下():
            '未知种类。上游这条路径直接抛 TypeError'
            状态['错误']=TypeError(未知种类前缀+str(消息))#兜底
        结算(记下)#结算

    def 当错误(错误):
        '子进程error事件原样拒绝'
        def 记下():
            '记下原错误'
            状态['错误']=错误#原样
        结算(记下)#结算

    def 当退出(码):
        '还没有结果就退出'
        def 记下():
            '没报告就退出'
            状态['错误']=目录选择器原生错误(提前退出文案)#失败
        结算(记下)#结算

    def 等中止():
        '信号置位后关窗口。立刻投一次，再按间隔重投，超过次数就杀掉子进程'
        while not 状态['已结算']:#还在选
            if not 信号.wait(中止轮询秒):#还没置位
                continue#再等
            with 互斥:#和结算串行，避免结算之后才开始关
                if 状态['已结算']:#已经有结果
                    return#停止监视
                停=事件()#结算时叫醒
                状态['定时']=停#交给结算
            次数=0#已计入的间隔次数
            投关闭()#立刻一次，不计入次数
            while not 停.wait(间隔秒):#间隔
                if 状态['已结算']:#已经有结果
                    return#停
                次数=次数+1#加一
                if 次数>关闭最多:#预算用完
                    def 记下():
                        '杀掉没有回应的子进程并记失败'
                        状态['错误']=目录选择器原生错误(无回应文案)#失败
                        工人.kill()#最后手段
                    结算(记下)#结算
                    return#停
                投关闭()#再投
            return#结算已经叫醒

    工人.on('message',当消息)#消息
    工人.on('error',当错误)#拉起失败
    工人.on('exit',当退出)#进程结束
    if 信号 is not None:#有寿命信号
        线程(target=等中止,daemon=True).start()#中止线程
    完成.wait()#等到结算
    if 状态['错误'] is not None:#失败
        raise 状态['错误']#抛给调用方
    return 状态['结果']#路径或 None
