'后台 bash 进程句柄的通用任务适配'
from ...沙盒.沙盒 import 沙箱拒绝标记,升级提示标记
import threading
from ...基础设施.js特性 import PromiseEX as 期约#期约封装

from .异常 import 后台错误#后台任务适配失败

__all__=['进程结果','进程源列表','环增量','进程作业']

def 沙箱说明列表(沙箱,升级模式=None):
    '值得写进终端细节的沙箱事实：运行器根本没跑命令，或一次拒绝（带本组合广告的升级提示）'
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
    非零命令退出只报告、不算失败，与前台渲染一致。沙箱事实并入细节
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
    """进程的非消费流读取器，作为注册表拉取源。
    惰性绑定：进程在 starter 内、登记准入之后才 spawn
    """
    def 源(通道):
        '一路流的拉取源'
        def 读取(起始字节):
            '发送尚未开始则交空'
            活=取进程()
            if 活 is None:
                return {'text':'','nextOffset':起始字节,'lossy':False}
            return 活.observed[通道].自偏移读取(起始字节)
        return {'channel':通道,'read':读取}
    return [源('stdout'),源('stderr')]

def 环增量(分块列表):
    '一次消费型注册表读取的环分块，按外壳工具渲染进程读取：先标准输出，再整段 `[stderr]`'
    出=''.join(块['text'] for 块 in 分块列表 if 块.get('channel')!='stderr')
    误=''.join(块['text'] for 块 in 分块列表 if 块.get('channel')=='stderr')
    分隔='\n' if len(出)>0 and not 出.endswith('\n') else ''
    return 出+(分隔+'[stderr]\n'+误 if len(误)>0 else '')

def 进程作业(启动,结局):
    """任务准入之后适配外壳准备，不暴露半拉进程。
    启动接收任务拥有的取消信号
    """
    取消事件=threading.Event()#任务拥有的取消信号
    进程=None#已启动的进程
    杀死错误=None#启动后补杀失败，进程关闭后再报告
    完成=期约()#任务结局，永不拒绝
    def 失败收尾(错误):
        '准备或结算失败：取消且尚无进程算 killed，否则 failed'
        状态='killed' if 取消事件.is_set() and 进程 is None else 'failed'
        完成.解决({'status':状态,'detail':str(错误)})
    def 进程已关闭(*关闭值):
        '进程关闭后投影结局；补杀失败则按失败结局'
        if 杀死错误 is not None:#补杀失败
            失败收尾(杀死错误)
            return
        try:#投影结局
            结局值=结局(进程)
        except Exception as 错误:#投影失败
            失败收尾(错误)
            return
        完成.解决(结局值)
    try:#准备并启动进程
        进程=启动(取消事件)
    except Exception as 错误:#准备失败
        失败收尾(错误)
    else:#已启动
        try:#取消已先到则补杀
            if 取消事件.is_set():
                进程.杀死()
        except Exception as 错误:#补杀失败也要等进程关闭
            杀死错误=错误
        进程.done.然后(进程已关闭,失败收尾)#等进程关闭
    def 取消(原因=None):
        '请求取消；已取消则空操作'
        if 取消事件.is_set():
            return
        取消事件.set()
        if 进程 is not None:
            进程.杀死()
    return {'cancel':取消,'done':完成}
