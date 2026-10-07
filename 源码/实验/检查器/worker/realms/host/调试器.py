from ......基础设施.js特性 import PromiseEX as 期约扩展#后端方法的返回期约
from ....异常 import 检查器错误#包内错误
from .值 import 可选原生字段,要求原生记录#值工具
from .桥接 import Host通知通道#通知通道
from .脚本 import Host脚本键#脚本键

__all__=['Host调试器后端']#仅中文公开名

class Host调试器后端:#Host Debugger后端
    '适配到公共命令、Runtime 值与事件的原生 Host 调试器'
    def __init__(自身,目标,运行时):#构造
        '装配通知通道'
        自身.目标=目标#会话
        自身.运行时=运行时#Runtime
        自身._事件=Host通知通道(目标,自身._接受,自身._投影)#通道

    def _接受(自身,消息):#是否接受
        '只收 Debugger 恢复、断点解析与暂停'
        return 消息.get('method') in ('Debugger.resumed','Debugger.breakpointResolved','Debugger.paused')#过滤

    def _投影(自身,消息):#投影
        '按方法投影，返回期约，兑现值是事件或 None'
        方法=消息.get('method')#方法
        if 方法=='Debugger.resumed':#恢复
            事件={'type':'resumed'}#恢复
        elif 方法=='Debugger.breakpointResolved':#断点解析
            事件=_断点已解析(消息['params'] if 'params' in 消息 else None)#断点解析
        else:#暂停需要异步转换远程对象
            return 自身._暂停(消息['params'] if 'params' in 消息 else None)#暂停
        已投影=期约扩展()#同步可得的事件期约
        已投影.解决(事件)#事件已就绪，直接解决
        return 已投影#返回已解决的期约

    def 启用(自身,请求):#启用
        'Debugger.enable，返回期约'
        return 自身.目标.请求('Debugger.enable',{**可选原生字段('maxScriptsCacheSize',请求['maxScriptsCacheSize'] if 'maxScriptsCacheSize' in 请求 else None)})#请求

    def 禁用(自身):#禁用
        'Debugger.disable，返回期约'
        return 自身.目标.请求('Debugger.disable',{})#请求

    def 暂停(自身):#暂停
        'Debugger.pause，返回期约'
        return 自身.目标.请求('Debugger.pause',{})#请求

    def 恢复(自身,请求):#恢复
        'Debugger.resume，返回期约'
        return 自身.目标.请求('Debugger.resume',{**可选原生字段('terminateOnResume',请求['terminateOnResume'] if 'terminateOnResume' in 请求 else None)})#请求

    def 帧上求值(自身,请求):#在调用帧求值
        'Debugger.evaluateOnCallFrame，返回期约，兑现值是完成结果'
        return 自身.目标.请求('Debugger.evaluateOnCallFrame',{#求值
            'callFrameId':请求['callFrameId'],'expression':请求['expression'],#表达式
            **可选原生字段('objectGroup',请求['objectGroup'] if 'objectGroup' in 请求 else None),#对象组
            **可选原生字段('includeCommandLineAPI',请求['includeCommandLineAPI'] if 'includeCommandLineAPI' in 请求 else None),#命令行API
            **可选原生字段('silent',请求['silent'] if 'silent' in 请求 else None),#静默
            **可选原生字段('returnByValue',请求['returnByValue'] if 'returnByValue' in 请求 else None),#按值
            **可选原生字段('generatePreview',请求['generatePreview'] if 'generatePreview' in 请求 else None),#预览
            **可选原生字段('throwOnSideEffect',请求['throwOnSideEffect'] if 'throwOnSideEffect' in 请求 else None),#副作用抛
            **可选原生字段('timeout',请求['timeoutMs'] if 'timeoutMs' in 请求 else None),#超时
        }).然后(自身.运行时.完成)#请求完成后再转换

    def 订阅(自身,监听):#订阅
        '订阅调试事件'
        return 自身._事件.订阅(监听)#委托

    def 关闭(自身):#关闭
        '拆除原生通知订阅'
        自身._事件.关闭()#关通道

    def _暂停(自身,参数):#暂停事件
        '投影 Debugger.paused，返回期约，兑现值是事件或 None'
        if 参数 is None:#无参数
            参数={}#空映射
        if 'callFrames' not in 参数 or not isinstance(参数['callFrames'],list) or not isinstance(参数.get('reason'),str):#无效
            无事件=期约扩展()#无效通知的期约
            无事件.解决(None)#无效通知不产出事件
            return 无事件#返回已解决的期约
        def 组装事件(调用帧):#全部调用帧转换完成后调用
            '组装暂停事件'
            事件={'type':'paused','callFrames':调用帧,'reason':参数['reason']}#暂停事件
            if 'data' in 参数 and 参数['data'] is not None:#可选数据
                事件['data']=参数['data']#写入
            命中=参数['hitBreakpoints'] if 'hitBreakpoints' in 参数 else None#命中断点
            if isinstance(命中,list) and all(isinstance(项,str) for 项 in 命中):#断点列表
                事件['hitBreakpoints']=命中#含
            if 'asyncStackTrace' in 参数 and 参数['asyncStackTrace'] is not None:#异步栈
                事件['asyncStackTrace']=自身.运行时.栈跟踪(参数['asyncStackTrace'])#含
            return 事件#返回
        return 期约扩展.全部([自身._调用帧(帧) for 帧 in 参数['callFrames']]).然后(组装事件)#各帧并发转换

    def _调用帧(自身,值):#调用帧
        '转换调用帧，返回期约'
        记录=要求原生记录(值,'Host Debugger call frame')#记录
        if not isinstance(记录.get('callFrameId'),str) or not isinstance(记录.get('functionName'),str) or not isinstance(记录.get('url'),str) or 'scopeChain' not in 记录 or not isinstance(记录['scopeChain'],list):#无效
            raise 检查器错误('Host Debugger returned an invalid call frame')#无效
        def 组装帧(转换结果):#作用域链与 this 转换完成后调用
            '组装调用帧，再转换返回值'
            作用域链,此对象=转换结果#作用域链与 this
            帧={#帧
                'callFrameId':记录['callFrameId'],'functionName':记录['functionName'],#名
                'location':_位置(记录['location']),'url':记录['url'],#位置
                'scopeChain':作用域链,'thisObject':此对象,#作用域与 this
            }#帧结束
            if 'functionLocation' in 记录 and 记录['functionLocation'] is not None:#函数位置
                帧['functionLocation']=_位置(记录['functionLocation'])#写入
            return 自身.运行时.填充远程对象(帧,记录,('returnValue',))#返回值转成远程对象
        return 期约扩展.全部([#作用域链与 this 并发转换
            期约扩展.全部([自身._作用域(项) for 项 in 记录['scopeChain']]),#作用域链
            自身.运行时.远程对象(记录['this'] if 'this' in 记录 else None),#this
        ]).然后(组装帧)#转换完成后再组装

    def _作用域(自身,值):#作用域
        '转换作用域，返回期约'
        记录=要求原生记录(值,'Host Debugger scope')#记录
        if not isinstance(记录.get('type'),str):#无效
            raise 检查器错误('Host Debugger returned an invalid scope')#无效
        def 组装作用域(对象):#作用域对象转换完成后调用
            '组装作用域'
            作用域={'type':记录['type'],'object':对象}#作用域
            if isinstance(记录.get('name'),str):#名
                作用域['name']=记录['name']#写入
            if 'startLocation' in 记录 and 记录['startLocation'] is not None:#起始
                作用域['startLocation']=_位置(记录['startLocation'])#写入
            if 'endLocation' in 记录 and 记录['endLocation'] is not None:#结束
                作用域['endLocation']=_位置(记录['endLocation'])#写入
            return 作用域#返回
        return 自身.运行时.远程对象(记录['object'] if 'object' in 记录 else None).然后(组装作用域)#对象转换完成后再组装

def _断点已解析(参数):#断点已解析
    '投影 breakpointResolved'
    if 参数 is None:#无参数
        参数={}#空映射
    if not isinstance(参数.get('breakpointId'),str) or 'location' not in 参数 or 参数['location'] is None:#无效
        return None#无
    return {'type':'breakpoint-resolved','breakpointId':参数['breakpointId'],'location':_位置(参数['location'])}#事件

def _位置(值):#位置
    '转换调试位置'
    记录=要求原生记录(值,'Host Debugger location')#记录
    行号=记录['lineNumber'] if 'lineNumber' in 记录 else None#行号
    if not isinstance(记录.get('scriptId'),str) or not isinstance(行号,int) or isinstance(行号,bool):#无效
        raise 检查器错误('Host Debugger returned an invalid location')#无效
    位置={'scriptKey':Host脚本键(记录['scriptId']),'lineNumber':行号}#位置
    列号=记录['columnNumber'] if 'columnNumber' in 记录 else None#列号
    if isinstance(列号,int) and not isinstance(列号,bool):#列
        位置['columnNumber']=列号#写入
    return 位置#返回
