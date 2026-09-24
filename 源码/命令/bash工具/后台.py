"""后台 bash 进程句柄的通用任务适配。"""
from ...沙盒.沙盒 import 沙箱拒绝标记,升级提示标记
import threading
from concurrent.futures import Future as 原生结果

__all__=['进程结果','进程源列表','环增量','进程作业']

class 后台错误(Exception):
    """后台任务适配失败。"""
    def __init__(自身,消息):
        """用原样英文消息构造。"""
        super().__init__(消息)

class 操作任务:
    """任务对象只留等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身.未来=原生结果()

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身.未来.done():
            自身.未来.set_result(值)
        return 值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身.未来.done():
            if isinstance(错误,BaseException):
                自身.未来.set_exception(错误)
            else:
                自身.未来.set_exception(后台错误(错误))

    def 等待(自身,超时=None):
        """阻塞到结算。"""
        return 自身.未来.result(timeout=超时)

def 沙箱说明列表(沙箱,升级模式=None):
    """值得写进终端细节的沙箱事实：运行器根本没跑命令，或一次拒绝（带本组合广告的升级提示）。"""
    if 升级模式 is None:
        升级模式=[]
    if 沙箱 is None:
        return []
    if 沙箱.get('runnerFailed') is True:
        return ['[sandbox: the sandbox runner itself failed under '+str(沙箱['mode'])+' mode — the command did not run; this is a sandbox problem, not a command failure]']
    if 沙箱.get('denied') is True:
        说明=[沙箱拒绝标记(沙箱['mode'])]
        if len(升级模式)>0:
            说明.append(升级提示标记('command'))
        return 说明
    return []

def 进程结果(进程,升级模式=None):
    """把已结算的后台进程映射到通用任务结果词。

    `killed` 仍是 killed（详情为已知信号），其余为带退出码详情的 completed。
    非零命令退出只报告、不算失败，与前台渲染一致。沙箱事实并入细节。
    """
    if 升级模式 is None:
        升级模式=[]
    if 进程.status=='killed':
        信号=进程.signal
        if 信号 is not None:
            基={'status':'killed','detail':'signal: '+str(信号)}
        else:
            基={'status':'killed','detail':'killed before exit'}
    else:
        退出码=进程.exitCode
        if 退出码 is None:
            退出码=0
        基={'status':'completed','detail':'exit code: '+str(退出码)}
    说明=沙箱说明列表(getattr(进程,'sandbox',None),升级模式)
    if len(说明)==0:
        return 基
    下一=dict(基)
    下一['detail']=基['detail']+'; '+' '.join(说明)
    return 下一

def 进程源列表(取进程):
    """进程的非消费流读取器，作为注册表拉取源。惰性绑定：进程在 starter 内、登记准入之后才 spawn。"""
    def 源(通道):
        """一路流的拉取源。"""
        def 读取(起始字节):
            """发送尚未开始则交空。"""
            活=取进程()
            if 活 is None:
                return {'text':'','nextOffset':起始字节,'lossy':False}
            return 活.observed[通道].自偏移读取(起始字节)
        return {'channel':通道,'read':读取}
    return [源('stdout'),源('stderr')]

def 环增量(分块列表):
    """一次消费型注册表读取的环分块，按外壳工具渲染进程读取：先标准输出，再整段 `[stderr]`。"""
    出=''.join(块['text'] for 块 in 分块列表 if 块.get('channel')!='stderr')
    误=''.join(块['text'] for 块 in 分块列表 if 块.get('channel')=='stderr')
    分隔='\n' if len(出)>0 and not 出.endswith('\n') else ''
    return 出+(分隔+'[stderr]\n'+误 if len(误)>0 else '')

def 进程作业(启动,结局):
    """任务准入之后适配外壳准备，不暴露半拉进程。启动接收任务拥有的取消信号。"""
    取消事件=threading.Event()
    进程箱=[None]
    完成=操作任务()
    def 体():
        """准备、可选杀死、等待关闭，再投影结局。"""
        try:
            进程箱[0]=启动(取消事件)
            进程=进程箱[0]
            try:
                if 取消事件.is_set():
                    进程.杀死()
            finally:
                进程.done.等待()
            完成.兑现(结局(进程))
        except BaseException as 错误:
            状态='killed' if 取消事件.is_set() and 进程箱[0] is None else 'failed'
            完成.兑现({'status':状态,'detail':str(错误)})
    工作=threading.Thread(target=体)
    工作.daemon=True
    工作.start()
    def 取消(原因=None):
        """请求取消；已取消则空操作。"""
        if 取消事件.is_set():
            return
        取消事件.set()
        if 进程箱[0] is not None:
            进程箱[0].杀死()
    return {'cancel':取消,'done':完成}
