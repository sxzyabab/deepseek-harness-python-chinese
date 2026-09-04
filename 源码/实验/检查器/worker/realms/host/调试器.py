"""一个原生 Node inspector 会话上的 DebuggerBackend 实现。"""
#对齐上游 worker/realms/host/debugger.ts

from ......内核.智能体循环.辅助 import 解开#可等待则等待
from .值 import 可选原生字段,要求原生记录#值工具
from .桥接 import Host通知通道#通知通道
from .脚本 import Host脚本键#脚本键

__all__=['Host调试器后端']#仅中文公开名

class Host调试器后端:#Host调试器后端
    """适配到公共命令、Runtime 值与事件的原生 Host 调试器。"""
    def __init__(自身,目标,运行时):#构造
        """装配通知通道。"""
        自身.目标=目标#会话
        自身.运行时=运行时#Runtime
        自身._事件=Host通知通道(#通道
            目标,#会话
            lambda 消息:消息.get('method') in ('Debugger.resumed','Debugger.breakpointResolved','Debugger.paused'),#过滤
            自身._投影,#投影
        )#通道结束

    def _投影(自身,消息):#投影
        """按方法投影。"""
        方法=消息.get('method')#方法
        if 方法=='Debugger.resumed':#恢复
            return {'type':'resumed'}#恢复
        if 方法=='Debugger.breakpointResolved':#断点解析
            return _断点已解析(消息.get('params'))#断点解析
        return 自身._暂停(消息.get('params'))#暂停

    def 启用(自身,请求):#启用
        """Debugger.enable。"""
        return 解开(自身.目标.请求('Debugger.enable',{**可选原生字段('maxScriptsCacheSize',请求.get('maxScriptsCacheSize'))}))#请求

    def 禁用(自身):#禁用
        """Debugger.disable。"""
        return 解开(自身.目标.请求('Debugger.disable',{}))#请求

    def 暂停(自身):#暂停
        """Debugger.pause。"""
        return 解开(自身.目标.请求('Debugger.pause',{}))#请求

    def 恢复(自身,请求):#恢复
        """Debugger.resume。"""
        return 解开(自身.目标.请求('Debugger.resume',{**可选原生字段('terminateOnResume',请求.get('terminateOnResume'))}))#请求

    def 帧上求值(自身,请求):#在调用帧求值
        """Debugger.evaluateOnCallFrame。"""
        return 解开(自身.运行时.完成(解开(自身.目标.请求('Debugger.evaluateOnCallFrame',{#求值
            'callFrameId':请求['callFrameId'],'expression':请求['expression'],#表达式
            **可选原生字段('objectGroup',请求.get('objectGroup')),#对象组
            **可选原生字段('includeCommandLineAPI',请求.get('includeCommandLineAPI')),#命令行API
            **可选原生字段('silent',请求.get('silent')),#静默
            **可选原生字段('returnByValue',请求.get('returnByValue')),#按值
            **可选原生字段('generatePreview',请求.get('generatePreview')),#预览
            **可选原生字段('throwOnSideEffect',请求.get('throwOnSideEffect')),#副作用抛
            **可选原生字段('timeout',请求.get('timeoutMs')),#超时
        }))))#completion结束

    def 订阅(自身,监听):#订阅
        """订阅调试事件。"""
        return 自身._事件.订阅(监听)#委托

    def 关闭(自身):#关闭
        """释放原生通知订阅。"""
        自身._事件.关闭()#关通道

    def _暂停(自身,参数):#暂停事件
        """投影 Debugger.paused。"""
        参数=参数 or {}#参数
        if not isinstance(参数.get('callFrames'),list) or not isinstance(参数.get('reason'),str):#无效
            return None#无
        调用帧=[自身._调用帧(帧) for 帧 in 参数['callFrames']]#帧
        事件={'type':'paused','callFrames':调用帧,'reason':参数['reason']}#暂停事件
        数据=参数.get('data')#数据
        if 数据 is not None:#可选数据
            事件['data']=数据#写入
        命中=参数.get('hitBreakpoints')#命中断点
        if isinstance(命中,list) and all(isinstance(项,str) for 项 in 命中):#断点列表
            事件['hitBreakpoints']=命中#含
        if 参数.get('asyncStackTrace') is not None:#异步栈
            事件['asyncStackTrace']=自身.运行时.栈跟踪(参数['asyncStackTrace'])#含
        return 事件#返回

    def _调用帧(自身,值):#调用帧
        """转换调用帧。"""
        记录=要求原生记录(值,'Host Debugger call frame')#记录
        if not isinstance(记录.get('callFrameId'),str) or not isinstance(记录.get('functionName'),str) or not isinstance(记录.get('url'),str) or not isinstance(记录.get('scopeChain'),list):#无效
            raise RuntimeError('Host Debugger returned an invalid call frame')#无效
        帧={#帧
            'callFrameId':记录['callFrameId'],'functionName':记录['functionName'],#名
            'location':_位置(记录['location']),'url':记录['url'],#位置
            'scopeChain':[自身._作用域(项) for 项 in 记录['scopeChain']],#作用域
            'thisObject':解开(自身.运行时.远程对象(记录.get('this'))),#this
        }#帧结束
        if 记录.get('functionLocation') is not None:#函数位置
            帧['functionLocation']=_位置(记录['functionLocation'])#写入
        if 记录.get('returnValue') is not None:#返回值
            帧['returnValue']=解开(自身.运行时.远程对象(记录['returnValue']))#写入
        return 帧#返回

    def _作用域(自身,值):#作用域
        """转换作用域。"""
        记录=要求原生记录(值,'Host Debugger scope')#记录
        if not isinstance(记录.get('type'),str):#无效
            raise RuntimeError('Host Debugger returned an invalid scope')#无效
        作用域={'type':记录['type'],'object':解开(自身.运行时.远程对象(记录.get('object')))}#作用域
        if isinstance(记录.get('name'),str):#名
            作用域['name']=记录['name']#写入
        if 记录.get('startLocation') is not None:#起始
            作用域['startLocation']=_位置(记录['startLocation'])#写入
        if 记录.get('endLocation') is not None:#结束
            作用域['endLocation']=_位置(记录['endLocation'])#写入
        return 作用域#返回

def _断点已解析(参数):#断点已解析
    """投影 breakpointResolved。"""
    参数=参数 or {}#参数
    if not isinstance(参数.get('breakpointId'),str) or 参数.get('location') is None:#无效
        return None#无
    return {'type':'breakpoint-resolved','breakpointId':参数['breakpointId'],'location':_位置(参数['location'])}#事件

def _位置(值):#位置
    """转换调试位置。"""
    记录=要求原生记录(值,'Host Debugger location')#记录
    if not isinstance(记录.get('scriptId'),str) or not isinstance(记录.get('lineNumber'),int):#无效
        raise RuntimeError('Host Debugger returned an invalid location')#无效
    位置={'scriptKey':Host脚本键(记录['scriptId']),'lineNumber':记录['lineNumber']}#位置
    if isinstance(记录.get('columnNumber'),int):#列
        位置['columnNumber']=记录['columnNumber']#写入
    return 位置#返回
