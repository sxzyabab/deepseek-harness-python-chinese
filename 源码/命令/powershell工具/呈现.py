"""pwsh 工具面向模型的结果渲染——`tool_bash` 渲染器的 PowerShell 成对实现。

对齐上游 `tool-pwsh/src/render.ts`。公开面仅中文名；无英文别名。
标准输出、带标记的标准错误段、沙箱拒绝/运行器失败标记（含同轮升级提示）、带溢出路径的截断通知，然后是退出状态标记。非零退出只报告、不标错——由模型决定如何反应；只有基础设施失败（启动错误、中止）才以 isError 结果出现。
"""
from ..沙盒 import (
    升级提示标记,#升级提示标记
    沙箱拒绝标记,#沙箱拒绝标记
)#导入升级提示与拒绝标记

__all__=('渲染Pwsh结果','渲染Pwsh进程读取')#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 流文本(输出):#一路流的面向模型文本
    """把截断通知（含完整输出溢出路径）追加到某路流的文本。"""
    if not 取字段(输出,'truncated'):#未截断
        return 取字段(输出,'text')#原样
    溢出=取字段(输出,'spillPath')#溢出路径
    if 溢出 is None:#没有溢出路径
        溢出='(unavailable)'#不可用占位
    return 取字段(输出,'text')+'\n[output truncated; full output: '+溢出+']'#截断则追加溢出路径

def 渲染Pwsh结果(结果,升级模式=None):#渲染前台pwsh结果
    """把一次已结束运行收成模型可见文本：标准输出，然后带标记的标准错误段，然后退出状态标记，与 bash 工具叙事一致——干净退出（0、无信号）不产生标记。"""
    if 升级模式 is None:#缺省空表
        升级模式=[]#无升级提示
    出=流文本(取字段(结果,'stdout'))#标准输出文本
    错=流文本(取字段(结果,'stderr'))#标准错误文本
    正文=出#正文从标准输出起
    if len(错)>0:#有标准错误
        if len(正文)>0 and (not 正文.endswith('\n')):#正文无结尾换行
            正文+='\n'#补换行
        正文+='[stderr]\n'+错#追加标准错误段
    if len(正文)==0:#两路皆空
        正文='(no output)'#占位
    标记们=[]#退出与沙箱标记
    沙箱=取字段(结果,'sandbox')#可选沙箱事实
    if 取字段(沙箱,'denied'):#沙箱拒绝
        标记们.append(沙箱拒绝标记(取字段(沙箱,'mode')))#写入拒绝标记
        if len(升级模式)>0:#有升级目标
            标记们.append(升级提示标记('command'))#追加命令升级提示
    if 取字段(结果,'timedOut'):#超时
        标记们.append('[timed out after '+str(取字段(结果,'timeoutMs'))+'ms]')#超时标记
    信号=取字段(结果,'signal')#终止信号
    if 信号 is not None:#被信号杀死
        标记们.append('[killed by signal: '+str(信号)+']')#信号标记
    elif 取字段(结果,'exitCode')!=0:#非零退出
        标记们.append('[exit code: '+str(取字段(结果,'exitCode'))+']')#退出码标记
    if len(标记们)==0:#无标记
        return 正文#只返回正文
    if not 正文.endswith('\n'):#标记前确保换行
        正文=正文+'\n'#补换行
    return 正文+'\n'.join(标记们)#正文后接各标记

def 渲染Pwsh进程读取(读取,沙箱=None,升级模式=None):#渲染后台进程增量
    """把一次后台进程读取收成模型可见的 `job_output` 增量：增量正文，并在内存截断丢掉未读字节时附上有损读取通知（含完整流溢出路径）。"""
    if 升级模式 is None:#缺省空表
        升级模式=[]#无升级提示
    通知们=[]#附加通知
    if 取字段(读取,'lossy'):#内存有损
        路径们=[]#溢出路径表
        出溢=取字段(读取,'stdoutSpillPath')#标准输出溢出
        错溢=取字段(读取,'stderrSpillPath')#标准错误溢出
        if 出溢 is not None:#有标准输出溢出
            路径们.append(出溢)#收下
        if 错溢 is not None:#有标准错误溢出
            路径们.append(错溢)#收下
        if len(路径们)>0:#有路径
            路径文=', '.join(路径们)#拼路径
        else:#没有路径
            路径文='(unavailable)'#不可用占位
        通知们.append('[some output was dropped from memory; full output: '+路径文+']')#有损读取通知
    if 取字段(沙箱,'runnerFailed'):#运行器自己失败
        通知们.append('[sandbox: the sandbox runner itself failed under '+str(取字段(沙箱,'mode'))+' mode — the command did not run; this is a sandbox problem, not a command failure]')#运行器失败通知
    elif 取字段(沙箱,'denied'):#沙箱拒绝
        通知们.append(沙箱拒绝标记(取字段(沙箱,'mode')))#拒绝标记
        if len(升级模式)>0:#有升级目标
            通知们.append(升级提示标记('command'))#命令升级提示
    增量=取字段(读取,'delta')#增量正文
    if 增量 is None:#缺增量
        增量=''#空串
    if len(通知们)==0:#无通知
        return 增量#只返回增量
    if len(增量)>0 and (not 增量.endswith('\n')):#增量非空且无结尾换行
        分隔='\n'#插换行
    else:#已换行或为空
        分隔=''#不插
    return 增量+分隔+'\n'.join(通知们)#增量后接通知
