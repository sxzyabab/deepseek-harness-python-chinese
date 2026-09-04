"""路由到 Client realm 的 CDP Runtime 参数校验与规范化。

对齐上游 `worker/cdp/domains/runtime/cdp-params.ts`。公开面仅中文名。
"""
from .....共享.json import 是否json值,是否普通对象#JSON工具
from .....共享.校验 import 精确键,可选布尔,可选字符串#校验

__all__=[#仅中文公开名
    '解析求值','解析取属性','解析调函数','解析等Promise',
    '解析释放对象','解析释放对象组','解析全局词法作用域名',
]#公开面结束

def 解析求值(参数):#解析求值
    """解析按 realm 路由的 Runtime.evaluate 参数。"""
    精确键(参数,[#精确键
        'expression','objectGroup','includeCommandLineAPI','silent','contextId','returnByValue',#常用
        'generatePreview','userGesture','awaitPromise','throwOnSideEffect','timeout','disableBreaks',#更多
        'replMode','allowUnsafeEvalBlockedByCSP','uniqueContextId','serializationOptions',#其余
    ],'Runtime.evaluate params')#标签
    if not isinstance(参数.get('expression'),str):#表达式
        raise Exception('Runtime.evaluate expression must be a string')#抛错
    选择器=解析上下文选择器(参数,'contextId')#选择器
    超时=参数.get('timeout')#超时
    if 超时 is not None and (not isinstance(超时,(int,float)) or isinstance(超时,bool) or not (超时==超时) or 超时<0):#非法
        raise Exception('Runtime.evaluate timeout must be a non-negative finite number')#抛错
    请求={#请求
        'expression':参数['expression'],#表达式
        **可选字符串(参数,'objectGroup'),#对象组
        **可选布尔(参数,'includeCommandLineAPI'),#命令行API
        **可选布尔(参数,'silent'),#静默
        **可选布尔(参数,'returnByValue'),#按值
        **可选布尔(参数,'generatePreview'),#预览
        **可选布尔(参数,'userGesture'),#手势
        **可选布尔(参数,'awaitPromise'),#等Promise
        **可选布尔(参数,'disableBreaks'),#禁断点
        **可选布尔(参数,'replMode'),#REPL
        **可选布尔(参数,'allowUnsafeEvalBlockedByCSP'),#CSP
        **可选布尔(参数,'throwOnSideEffect'),#副作用
        **可选json对象(参数,'serializationOptions'),#序列化
    }#request结束
    if 超时 is not None:#有超时
        请求['timeoutMs']=超时#超时毫秒
    return {**选择器,'request':请求}#返回结束

def 解析取属性(参数):#解析取属性
    """解析按 realm 路由的 Runtime.getProperties 参数。"""
    精确键(参数,[#精确键
        'objectId','ownProperties','accessorPropertiesOnly','generatePreview','nonIndexedPropertiesOnly',#字段
    ],'Runtime.getProperties params')#标签
    if not isinstance(参数.get('objectId'),str):#类型
        raise Exception('Runtime.getProperties objectId must be a string')#抛错
    return {#结果
        'objectId':参数['objectId'],#对象id
        'request':{#请求
            **可选布尔(参数,'ownProperties'),#自有属性
            **可选布尔(参数,'accessorPropertiesOnly'),#仅访问器
            **可选布尔(参数,'generatePreview'),#预览
            **可选布尔(参数,'nonIndexedPropertiesOnly'),#非索引
        },#request结束
    }#返回结束

def 解析调函数(参数):#解析调函数
    """解析按 Client 路由的 Runtime.callFunctionOn 参数。"""
    精确键(参数,[#精确键
        'functionDeclaration','objectId','arguments','silent','returnByValue','generatePreview','userGesture',#常用
        'awaitPromise','executionContextId','objectGroup','throwOnSideEffect','uniqueContextId','serializationOptions',#其余
    ],'Runtime.callFunctionOn params')#标签
    if not isinstance(参数.get('functionDeclaration'),str):#函数声明
        raise Exception('Runtime.callFunctionOn functionDeclaration must be a string')#抛错
    选择器=解析上下文选择器(参数,'executionContextId')#选择器
    对象id=可选对象id(参数.get('objectId'),'Runtime.callFunctionOn objectId')#对象id
    if 对象id is None and 选择器.get('executionContextId') is None and 选择器.get('uniqueContextId') is None:#要求
        raise Exception('Runtime.callFunctionOn requires objectId or an execution context')#抛错
    if 对象id is not None and (选择器.get('executionContextId') is not None or 选择器.get('uniqueContextId') is not None):#互斥
        raise Exception('Runtime.callFunctionOn objectId and execution context are mutually exclusive')#抛错
    参数们=[]#参数
    if 'arguments' in 参数:#有参数
        if not isinstance(参数['arguments'],list):#类型
            raise Exception('Runtime.callFunctionOn arguments must be an array')#抛错
        参数们=[解析调用参数(项) for 项 in 参数['arguments']]#解析每项
    结果={**选择器,'arguments':参数们,'request':{#结果
        'functionDeclaration':参数['functionDeclaration'],#函数声明
        **可选字符串(参数,'objectGroup'),#对象组
        **可选布尔(参数,'silent'),#静默
        **可选布尔(参数,'returnByValue'),#按值
        **可选布尔(参数,'generatePreview'),#预览
        **可选布尔(参数,'userGesture'),#手势
        **可选布尔(参数,'awaitPromise'),#等Promise
        **可选布尔(参数,'throwOnSideEffect'),#副作用
        **可选json对象(参数,'serializationOptions'),#序列化
    }}#结果结束
    if 对象id is not None:#有对象id
        结果['objectId']=对象id#写入
    return 结果#返回

def 解析等Promise(参数):#解析等Promise
    """解析按 Client 路由的 Runtime.awaitPromise 参数。"""
    精确键(参数,['promiseObjectId','returnByValue','generatePreview'],'Runtime.awaitPromise params')#键
    if not isinstance(参数.get('promiseObjectId'),str):#类型
        raise Exception('Runtime.awaitPromise promiseObjectId must be a string')#抛错
    return {#结果
        'promiseObjectId':参数['promiseObjectId'],#Promise id
        'request':{#请求
            **可选布尔(参数,'returnByValue'),#按值
            **可选布尔(参数,'generatePreview'),#预览
        },#request结束
    }#返回结束

def 解析释放对象(参数):#解析释放对象
    """解析一个必需的对象 id。"""
    精确键(参数,['objectId'],'Runtime.releaseObject params')#键
    if not isinstance(参数.get('objectId'),str):#类型
        raise Exception('Runtime.releaseObject objectId must be a string')#抛错
    return 参数['objectId']#返回

def 解析释放对象组(参数):#解析释放组
    """解析一个必需的对象组名。"""
    精确键(参数,['objectGroup'],'Runtime.releaseObjectGroup params')#键
    if not isinstance(参数.get('objectGroup'),str):#类型
        raise Exception('Runtime.releaseObjectGroup objectGroup must be a string')#抛错
    return 参数['objectGroup']#返回

def 解析全局词法作用域名(参数):#解析词法名
    """解析 Runtime.globalLexicalScopeNames 的上下文选择。"""
    精确键(参数,['executionContextId'],'Runtime.globalLexicalScopeNames params')#键
    return 解析上下文选择器(参数,'executionContextId')#选择器

def 解析调用参数(值):#解析调用参数
    """解析 callFunctionOn 参数项。"""
    if not 是否普通对象(值):#非对象
        raise Exception('Runtime.callFunctionOn argument must be an object')#抛错
    精确键(值,['value','unserializableValue','objectId'],'Runtime.callFunctionOn argument')#键
    出现=[键 for 键 in ('value','unserializableValue','objectId') if 键 in 值]#出现的键
    if len(出现)>1:#多重
        raise Exception('Runtime.callFunctionOn argument has multiple value representations')#抛错
    if len(出现)==0:#无表示
        return {'kind':'undefined'}#undefined
    if 出现[0]=='value':#JSON值
        if not 是否json值(值['value']):#非JSON
            raise Exception('Runtime.callFunctionOn argument value must be JSON')#抛错
        return {'kind':'value','value':值['value']}#值
    if 出现[0]=='unserializableValue':#不可序列化
        if not isinstance(值['unserializableValue'],str):#类型
            raise Exception('Runtime.callFunctionOn unserializableValue must be a string')#抛错
        return {'kind':'unserializable','value':值['unserializableValue']}#不可序列化
    if not isinstance(值['objectId'],str):#类型
        raise Exception('Runtime.callFunctionOn argument objectId must be a string')#抛错
    return {'kind':'object','objectId':值['objectId']}#对象

def 解析上下文选择器(参数,数字键):#解析上下文选择器
    """解析数字或唯一上下文选择器。"""
    数字=参数.get(数字键)#数字值
    唯一=参数.get('uniqueContextId')#唯一值
    if 数字 is not None and (not isinstance(数字,int) or isinstance(数字,bool) or abs(数字)>9007199254740991):#非安全整数
        raise Exception(f'Runtime {数字键} must be an integer')#抛错
    if 唯一 is not None and not isinstance(唯一,str):#类型
        raise Exception('Runtime uniqueContextId must be a string')#抛错
    if 数字 is not None and 唯一 is not None:#互斥
        raise Exception('Runtime context selectors are mutually exclusive')#抛错
    结果={}#选择器
    if 数字 is not None:#有数字
        结果[数字键]=数字#写入
    if 唯一 is not None:#有唯一
        结果['uniqueContextId']=唯一#写入
    return 结果#返回

def 可选对象id(值,标签):#可选对象id
    """可选对象 id。"""
    if 值 is None:#缺省
        return None#无
    if not isinstance(值,str):#类型
        raise Exception(f'{标签} must be a string')#抛错
    return 值#返回

def 可选json对象(值,键):#可选JSON对象字段
    """可选 JSON 对象字段。"""
    if 键 not in 值:#缺省
        return {}#空
    项=值[键]#取值
    if not 是否普通对象(项) or not 是否json值(项):#非法
        raise Exception(f'Runtime {键} must be a JSON object')#抛错
    return {键:项}#字段
