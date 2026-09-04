"""realm 中立脚本与调试器事件的 CDP 投影。"""
#对齐上游 worker/cdp/domains/debugger/projector.ts

from .脚本注册表 import cdp脚本id#脚本id转换

__all__=['脚本已解析事件','调试器事件']#仅中文公开名

def 脚本已解析事件(realm,脚本):#脚本已解析事件
    """将一个通用脚本描述符投影为 Debugger.scriptParsed。"""
    上下文=脚本.get('executionContextId')#执行上下文
    if 上下文 is None and realm.context.kind=='synthetic':#合成
        上下文=realm.context.id#取id
    if 上下文 is None:#仍无
        上下文=0#默认0
    参数={#参数
        'scriptId':cdp脚本id(脚本['scriptKey']),#脚本id
        'url':脚本['url'],#URL
        'startLine':脚本['startLine'],#起始行
        'startColumn':脚本['startColumn'],#起始列
        'endLine':脚本['endLine'],#结束行
        'endColumn':脚本['endColumn'],#结束列
        'executionContextId':上下文,#执行上下文
        'hash':脚本.get('hash',''),#哈希
        'buildId':脚本.get('buildId') or '',#构建id
    }#参数结束
    if 'sourceMapUrl' in 脚本:#源映射
        参数['sourceMapURL']=脚本['sourceMapUrl']#写入
    if 'isModule' in 脚本:#是否模块
        参数['isModule']=脚本['isModule']#写入
    if 'length' in 脚本:#长度
        参数['length']=脚本['length']#写入
    return {'method':'Debugger.scriptParsed','params':参数}#通知

def _位置(值):#位置投影
    """投影调试位置。"""
    结果={'scriptId':cdp脚本id(值['scriptKey']),'lineNumber':值['lineNumber']}#位置对象
    if 'columnNumber' in 值:#列号
        结果['columnNumber']=值['columnNumber']#写入
    return 结果#返回

def _栈(值):#栈投影
    """投影栈跟踪。"""
    结果={}#栈对象
    if 'description' in 值:#描述
        结果['description']=值['description']#写入
    结果['callFrames']=[{#帧
        'functionName':帧['functionName'],#函数名
        'scriptId':cdp脚本id(帧['scriptKey']) if 'scriptKey' in 帧 else '',#脚本
        'url':帧['url'],#url
        'lineNumber':帧['lineNumber'],#行
        'columnNumber':帧['columnNumber'],#列
    } for 帧 in 值['callFrames']]#map
    if 'parent' in 值:#父栈
        结果['parent']=_栈(值['parent'])#递归
    return 结果#返回

def 调试器事件(realm,事件,运行时):#调试器事件投影
    """将一个通用调试器事件及其全部嵌套 Runtime 对象投影为 CDP。"""
    if 事件['type']=='resumed':#恢复
        return {'method':'Debugger.resumed','params':{}}#resumed通知
    if 事件['type']=='breakpoint-resolved':#断点解析
        return {#resolved通知
            'method':'Debugger.breakpointResolved',#方法
            'params':{'breakpointId':事件['breakpointId'],'location':_位置(事件['location'])},#参数
        }#return结束
    if 事件['type']!='paused':#未预期
        raise ValueError(f'Unexpected debugger event: {事件!r}')#断言
    调用帧=[]#帧列表
    for 帧 in 事件['callFrames']:#扫帧
        作用域链=[]#作用域
        for 作用域 in 帧['scopeChain']:#扫作用域
            项={#作用域项
                'type':作用域['type'],#类型
                'object':运行时.投影远程对象(realm,作用域['object'],'backtrace'),#对象
            }#项结束
            if 'name' in 作用域:#名称
                项['name']=作用域['name']#写入
            if 'startLocation' in 作用域:#起始
                项['startLocation']=_位置(作用域['startLocation'])#写入
            if 'endLocation' in 作用域:#结束
                项['endLocation']=_位置(作用域['endLocation'])#写入
            作用域链.append(项)#收集
        帧项={#调用帧
            'callFrameId':帧['callFrameId'],#帧id
            'functionName':帧['functionName'],#函数名
            'location':_位置(帧['location']),#位置
            'url':帧['url'],#URL
            'scopeChain':作用域链,#作用域链
            'this':运行时.投影远程对象(realm,帧['thisObject'],'backtrace'),#this
        }#帧项结束
        if 'functionLocation' in 帧:#函数位置
            帧项['functionLocation']=_位置(帧['functionLocation'])#写入
        if 'returnValue' in 帧:#返回值
            帧项['returnValue']=运行时.投影远程对象(realm,帧['returnValue'],'backtrace')#写入
        调用帧.append(帧项)#收集
    参数={'callFrames':调用帧,'reason':事件['reason']}#参数
    if 'data' in 事件:#数据
        参数['data']=事件['data']#写入
    if 'hitBreakpoints' in 事件:#命中断点
        参数['hitBreakpoints']=事件['hitBreakpoints']#写入
    if 'asyncStackTrace' in 事件:#异步栈
        参数['asyncStackTrace']=_栈(事件['asyncStackTrace'])#写入
    return {'method':'Debugger.paused','params':参数}#paused通知
