"""pwsh 工具面向模型的结果渲染——bash 渲染器的 PowerShell 成对实现。

标准输出、带标记的标准错误段、沙箱拒绝/运行器失败标记（含同轮升级提示）、带溢出路径的截断通知，然后是退出状态标记。非零退出只报告、不标错——由模型决定如何反应；只有基础设施失败（启动错误、中止）才以 isError 结果出现。
"""
from ...沙盒.沙盒 import (
    升级提示标记,#升级提示标记
    沙箱拒绝标记,#沙箱拒绝标记
)#导入升级提示与拒绝标记

__all__=('渲染Pwsh结果','渲染Pwsh晋升','渲染Pwsh任务读取')#仅中文公开名

def 流文本(输出):#一路流的面向模型文本
    """把截断通知（含完整输出溢出路径）追加到某路流的文本。"""
    if 输出['truncated'] is not True:#未截断
        return 输出['text']#原样
    溢出=输出['spillPath'] if 'spillPath' in 输出 else None#溢出路径
    if 溢出 is None:#没有溢出路径
        溢出='(unavailable)'#不可用占位
    return 输出['text']+'\n[output truncated; full output: '+溢出+']'#截断则追加溢出路径

def 渲染Pwsh结果(结果,升级模式=None):#渲染前台pwsh结果
    """把一次已结束运行收成模型可见文本：标准输出，然后带标记的标准错误段，然后退出状态标记，与 bash 工具叙事一致——干净退出（0、无信号）不产生标记。"""
    if 升级模式 is None:#缺省空表
        升级模式=[]#无升级提示
    标准输出文本=流文本(结果['stdout'])#标准输出文本
    标准误文本=流文本(结果['stderr'])#标准错误文本
    正文=标准输出文本#正文从标准输出起
    if len(标准误文本)>0:#有标准错误
        if len(正文)>0 and (not 正文.endswith('\n')):#正文无结尾换行
            正文+='\n'#补换行
        正文+='[stderr]\n'+标准误文本#追加标准错误段
    if len(正文)==0:#两路皆空
        正文='(no output)'#占位
    标记列表=[]#退出与沙箱标记
    沙箱=结果['sandbox'] if 'sandbox' in 结果 else None#可选沙箱事实
    if 沙箱 is not None and 沙箱['denied'] is True:#沙箱拒绝
        标记列表.append(沙箱拒绝标记(沙箱['mode']))#写入拒绝标记
        if len(升级模式)>0:#有升级目标
            标记列表.append(升级提示标记('command'))#追加命令升级提示
    if 结果['timedOut'] is True:#超时
        标记列表.append('[timed out after '+str(结果['timeoutMs'])+'ms]')#超时标记
    if 结果.get('stopped') is not None:
        标记列表.append('[stopped: '+str(结果['stopped'])+']')
    信号=结果['signal']#终止信号
    if 信号 is not None:#被信号杀死
        标记列表.append('[killed by signal: '+str(信号)+']')#信号标记
    elif 结果['exitCode']!=0:#非零退出
        标记列表.append('[exit code: '+str(结果['exitCode'])+']')#退出码标记
    if len(标记列表)==0:#无标记
        return 正文#只返回正文
    if not 正文.endswith('\n'):#标记前确保换行
        正文=正文+'\n'#补换行
    return 正文+'\n'.join(标记列表)#正文后接各标记

def 渲染Pwsh晋升(已晋升):
    """前台调用停止等待后模型看见的文本：已捕获输出，然后仍在运行标记与任务交接说明。"""
    输出=已晋升['output']
    if len(输出)>0:
        正文=输出 if 输出.endswith('\n') else 输出+'\n'
    else:
        正文=''
    return (正文+'[still running after '+str(已晋升['timeoutMs'])+'ms; moved to background job '+str(已晋升['jobId'])+']\n'
        +'The command keeps running in the background. You will be notified when it finishes; '
        +'read newer output with job_output, stop it with job_kill.')

def 渲染Pwsh任务读取(增量,有损,溢出路径,沙箱=None,升级模式=None):
    """前台调用停止等待时嵌入结果的那一次消费型注册表读取。"""
    if 升级模式 is None:
        升级模式=[]
    通知列表=[]
    if 有损 is True:
        路径文=', '.join(溢出路径) if len(溢出路径)>0 else '(unavailable)'
        通知列表.append('[some output was dropped from memory; full output: '+路径文+']')
    if 沙箱 is not None and 沙箱.get('runnerFailed') is True:
        通知列表.append('[sandbox: the sandbox runner itself failed under '+str(沙箱['mode'])+' mode — the command did not run; this is a sandbox problem, not a command failure]')
    elif 沙箱 is not None and 沙箱.get('denied') is True:
        通知列表.append(沙箱拒绝标记(沙箱['mode']))
        if len(升级模式)>0:
            通知列表.append(升级提示标记('command'))
    if len(通知列表)==0:
        return 增量
    分隔='\n' if len(增量)>0 and not 增量.endswith('\n') else ''
    return 增量+分隔+'\n'.join(通知列表)
