"""一个原生 Node inspector 会话上的 RuntimeBackend 实现。"""
#对齐上游 worker/realms/host/runtime.ts 段1

from ......内核.智能体循环.辅助 import 解开#可等待则等待
from .值 import 是否原生记录,可选原生字段,要求原生记录#值工具
from .脚本 import Host脚本键#脚本键

__all__=['Host运行时后端']#仅中文公开名

class Host运行时后端:#Host Runtime后端
    """在公共值背后保留原生 V8 语义的 Host Runtime 适配器。"""
    def __init__(自身,目标):#构造
        """观察上下文。"""
        自身.目标=目标#会话
        自身._默认上下文id=None#默认上下文id
        自身._取消订阅=目标.订阅(自身._观察上下文)#观察上下文

    def 启用(自身):#启用
        """Runtime.enable。"""
        解开(自身.目标.请求('Runtime.enable',{}))#请求

    def 禁用(自身):#禁用
        """Runtime.disable。"""
        解开(自身.目标.请求('Runtime.disable',{}))#请求
        自身._默认上下文id=None#清空默认

    def 求值(自身,请求):#求值
        """Runtime.evaluate。"""
        return 解开(自身.完成(解开(自身.目标.请求('Runtime.evaluate',{#完成
            'expression':请求['expression'],#表达式
            **(_原生上下文(请求.get('context'),'contextId') or {}),#上下文
            **可选原生字段('objectGroup',请求.get('objectGroup')),#对象组
            **可选原生字段('includeCommandLineAPI',请求.get('includeCommandLineAPI')),#命令行API
            **可选原生字段('silent',请求.get('silent')),#静默
            **可选原生字段('returnByValue',请求.get('returnByValue')),#按值
            **可选原生字段('generatePreview',请求.get('generatePreview')),#预览
            **可选原生字段('userGesture',请求.get('userGesture')),#手势
            **可选原生字段('awaitPromise',请求.get('awaitPromise')),#等Promise
            **可选原生字段('disableBreaks',请求.get('disableBreaks')),#禁用断点
            **可选原生字段('replMode',请求.get('replMode')),#REPL
            **可选原生字段('allowUnsafeEvalBlockedByCSP',请求.get('allowUnsafeEvalBlockedByCSP')),#CSP
            **可选原生字段('throwOnSideEffect',请求.get('throwOnSideEffect')),#副作用
            **可选原生字段('serializationOptions',请求.get('serializationOptions')),#序列化
            **可选原生字段('timeout',请求.get('timeoutMs')),#超时
        }))))#completion结束

    def 取属性(自身,请求):#取属性
        """Runtime.getProperties。"""
        响应=解开(自身.目标.请求('Runtime.getProperties',{#请求
            'objectId':请求['handle'],#对象id
            **可选原生字段('ownProperties',请求.get('ownProperties')),#自有
            **可选原生字段('accessorPropertiesOnly',请求.get('accessorPropertiesOnly')),#仅访问器
            **可选原生字段('generatePreview',请求.get('generatePreview')),#预览
            **可选原生字段('nonIndexedPropertiesOnly',请求.get('nonIndexedPropertiesOnly')),#非索引
        }))#request结束
        return 解开(自身._属性集(响应))#转换

    def 调函数(自身,请求):#调函数
        """Runtime.callFunctionOn。"""
        接收者=请求.get('receiver')#接收者
        上下文=None if 接收者 is not None else (_原生上下文(请求.get('context') or _默认上下文(自身._默认上下文id),'executionContextId'))#上下文
        if 接收者 is None and 上下文 is None:#不可用
            raise RuntimeError('Host Runtime default execution context is unavailable')#抛错
        参数={#请求
            'functionDeclaration':请求['functionDeclaration'],#函数声明
            **({'objectId':接收者} if 接收者 is not None else 上下文),#目标
            **可选原生字段('objectGroup',请求.get('objectGroup')),#对象组
            **可选原生字段('silent',请求.get('silent')),#静默
            **可选原生字段('returnByValue',请求.get('returnByValue')),#按值
            **可选原生字段('generatePreview',请求.get('generatePreview')),#预览
            **可选原生字段('userGesture',请求.get('userGesture')),#手势
            **可选原生字段('awaitPromise',请求.get('awaitPromise')),#等Promise
            **可选原生字段('throwOnSideEffect',请求.get('throwOnSideEffect')),#副作用
            **可选原生字段('serializationOptions',请求.get('serializationOptions')),#序列化
        }#参数结束
        if 请求.get('arguments') is not None:#有参数
            参数['arguments']=[_转原生参数(项) for 项 in 请求['arguments']]#参数
        return 解开(自身.完成(解开(自身.目标.请求('Runtime.callFunctionOn',参数))))#完成

    def 等Promise(自身,请求):#等Promise
        """Runtime.awaitPromise。"""
        return 解开(自身.完成(解开(自身.目标.请求('Runtime.awaitPromise',{#完成
            'promiseObjectId':请求['promise'],#Promise id
            **可选原生字段('returnByValue',请求.get('returnByValue')),#按值
            **可选原生字段('generatePreview',请求.get('generatePreview')),#预览
        }))))#completion结束

    def 全局词法名(自身,上下文=None):#全局词法名
        """Runtime.globalLexicalScopeNames。"""
        响应=解开(自身.目标.请求('Runtime.globalLexicalScopeNames',{#请求
            **(_原生上下文(上下文 or _默认上下文(自身._默认上下文id),'executionContextId') or {}),#上下文
        }))#request结束
        名字=响应.get('names')#名字
        if not isinstance(名字,list) or not all(isinstance(名,str) for 名 in 名字):#校验
            raise RuntimeError('Host Runtime returned invalid lexical scope names')#无效
        return 名字#名字

    def 释放对象(自身,句柄):#释放对象
        """Runtime.releaseObject。"""
        解开(自身.目标.请求('Runtime.releaseObject',{'objectId':句柄}))#请求

    def 释放对象组(自身,组):#释放对象组
        """Runtime.releaseObjectGroup。"""
        解开(自身.目标.请求('Runtime.releaseObjectGroup',{'objectGroup':组}))#请求

    def 关闭(自身):#关闭
        """释放本后端拥有的原生上下文观察者。"""
        自身._取消订阅()#取消订阅

    def 完成(自身,值):#完成
        """转换原生 Runtime 完成。"""
        输出={'result':解开(自身.远程对象(值.get('result')))}#结果
        if 值.get('exceptionDetails') is not None:#异常
            输出['exceptionDetails']=解开(自身.异常详情(值['exceptionDetails']))#含异常
        return 输出#返回

    def _属性集(自身,值):#属性集
        """转换属性结果。"""
        if not isinstance(值.get('result'),list):#无效
            raise RuntimeError('Host Runtime returned invalid properties')#无效
        输出={'properties':[解开(自身._属性(项)) for 项 in 值['result']]}#属性
        if 值.get('internalProperties') is not None:#内部
            输出['internalProperties']=解开(自身._内部属性(值['internalProperties']))#含
        if 值.get('privateProperties') is not None:#私有
            输出['privateProperties']=解开(自身._私有属性(值['privateProperties']))#含
        if 值.get('exceptionDetails') is not None:#异常
            输出['exceptionDetails']=解开(自身.异常详情(值['exceptionDetails']))#含
        return 输出#返回

    def _属性(自身,值):#属性描述符
        """转换属性描述符。"""
        记录=要求原生记录(值,'Host Runtime property descriptor')#记录
        if not isinstance(记录.get('name'),str) or not isinstance(记录.get('configurable'),bool) or not isinstance(记录.get('enumerable'),bool):#无效
            raise RuntimeError('Host Runtime returned invalid property descriptor')#无效
        描述符={**记录,'name':记录['name'],'configurable':记录['configurable'],'enumerable':记录['enumerable']}#描述符
        if 记录.get('value') is not None:#值
            描述符['value']=解开(自身.远程对象(记录['value']))#值
        if 记录.get('get') is not None:#getter
            描述符['get']=解开(自身.远程对象(记录['get']))#getter
        if 记录.get('set') is not None:#setter
            描述符['set']=解开(自身.远程对象(记录['set']))#setter
        if 记录.get('symbol') is not None:#符号
            描述符['symbol']=解开(自身.远程对象(记录['symbol']))#符号
        return 描述符#返回

    def _内部属性(自身,值):#内部属性
        """转换内部属性列表。"""
        if not isinstance(值,list):#无效
            raise RuntimeError('Host Runtime returned invalid internal properties')#无效
        结果=[]#列表
        for 项 in 值:#映射
            记录=要求原生记录(项,'Host Runtime internal property')#记录
            if not isinstance(记录.get('name'),str):#无效
                raise RuntimeError('Host Runtime returned invalid internal property')#无效
            描述符={'name':记录['name']}#描述符
            if 记录.get('value') is not None:#值
                描述符['value']=解开(自身.远程对象(记录['value']))#值
            结果.append(描述符)#收集
        return 结果#返回

    def _私有属性(自身,值):#私有属性
        """转换私有属性列表。"""
        if not isinstance(值,list):#无效
            raise RuntimeError('Host Runtime returned invalid private properties')#无效
        结果=[]#列表
        for 项 in 值:#映射
            记录=要求原生记录(项,'Host Runtime private property')#记录
            if not isinstance(记录.get('name'),str):#无效
                raise RuntimeError('Host Runtime returned invalid private property')#无效
            描述符={'name':记录['name']}#描述符
            if 记录.get('value') is not None:#值
                描述符['value']=解开(自身.远程对象(记录['value']))#值
            if 记录.get('get') is not None:#getter
                描述符['get']=解开(自身.远程对象(记录['get']))#getter
            if 记录.get('set') is not None:#setter
                描述符['set']=解开(自身.远程对象(记录['set']))#setter
            结果.append(描述符)#收集
        return 结果#返回

    def 异常详情(自身,值):#异常详情
        """转换原生异常详情。"""
        记录=要求原生记录(值,'Host Runtime exception details')#记录
        if not isinstance(记录.get('text'),str) or not isinstance(记录.get('lineNumber'),int) or not isinstance(记录.get('columnNumber'),int):#无效
            raise RuntimeError('Host Runtime returned invalid exception details')#无效
        详情={**记录,'text':记录['text'],'lineNumber':记录['lineNumber'],'columnNumber':记录['columnNumber']}#详情
        if 记录.get('stackTrace') is not None:#栈
            详情['stackTrace']=自身.栈跟踪(记录['stackTrace'])#栈
        if 记录.get('exception') is not None:#异常对象
            详情['exception']=解开(自身.远程对象(记录['exception']))#异常对象
        return 详情#返回

    def 远程对象(自身,值):#远程对象
        """转换原生 V8 RemoteObject。"""
        记录=要求原生记录(值,'Host Runtime RemoteObject')#记录
        if not isinstance(记录.get('type'),str):#无效
            raise RuntimeError('Host Runtime returned an invalid RemoteObject')#无效
        描述符={键:项 for 键,项 in 记录.items() if 键!='objectId'}#去掉objectId
        对象id=记录['objectId'] if isinstance(记录.get('objectId'),str) else None#对象id
        语义=None if 对象id is None else 自身._识别对象(对象id)#语义引用
        输出={'descriptor':描述符}#远程对象
        if 对象id is not None:#句柄
            输出['object']={'handle':对象id}#句柄
        if 语义 is not None:#语义
            输出['semanticReference']=语义#语义
        return 输出#返回

    def 栈跟踪(自身,值):#栈跟踪
        """转换原生栈跟踪。"""
        记录=要求原生记录(值,'Host Runtime stack trace')#记录
        if not isinstance(记录.get('callFrames'),list):#无效
            raise RuntimeError('Host Runtime returned an invalid stack trace')#无效
        帧们=[]#帧
        for 帧 in 记录['callFrames']:#帧
            字段=要求原生记录(帧,'Host Runtime call frame')#字段
            if not isinstance(字段.get('functionName'),str) or not isinstance(字段.get('url'),str) or not isinstance(字段.get('lineNumber'),int) or not isinstance(字段.get('columnNumber'),int):#无效
                raise RuntimeError('Host Runtime returned an invalid call frame')#无效
            项={'functionName':字段['functionName'],'url':字段['url'],'lineNumber':字段['lineNumber'],'columnNumber':字段['columnNumber']}#帧对象
            if isinstance(字段.get('scriptId'),str):#脚本
                项['scriptKey']=Host脚本键(字段['scriptId'])#键
            帧们.append(项)#收集
        栈={'callFrames':帧们}#栈
        if isinstance(记录.get('description'),str):#描述
            栈['description']=记录['description']#描述
        if 记录.get('parent') is not None:#父栈
            栈['parent']=自身.栈跟踪(记录['parent'])#父栈
        return 栈#返回

    def _观察上下文(自身,消息):#观察上下文
        """跟踪默认执行上下文。"""
        if 消息.get('method')=='Runtime.executionContextCreated':#创建
            上下文=消息.get('params',{}).get('context')#上下文
            上下文=上下文 if 是否原生记录(上下文) else None#上下文
            辅助=上下文.get('auxData') if 上下文 else None#辅助
            辅助=辅助 if 是否原生记录(辅助) else None#辅助
            if 上下文 is not None and 辅助 and 辅助.get('isDefault') is True and isinstance(上下文.get('id'),int):#默认
                自身._默认上下文id=上下文['id']#保存
            return#返回
        if 消息.get('method')!='Runtime.executionContextDestroyed':#非销毁
            return#返回
        if 消息.get('params',{}).get('executionContextId')==自身._默认上下文id:#清空
            自身._默认上下文id=None#清空

    def _识别对象(自身,对象id):#识别对象
        """可选语义识别。"""
        try:#可选语义
            响应=解开(自身.目标.请求('Runtime.callFunctionOn',{#调用识别函数
                'objectId':对象id,#对象
                'functionDeclaration':'function(){return this&&this.__dshObjectReference||null}',#识别函数占位
                'returnByValue':True,'silent':True,#静默
            }))#request结束
            if 响应.get('exceptionDetails') is not None or not 是否原生记录(响应.get('result')):#失败
                return None#无
            值=响应['result'].get('value')#值
            return None if 值 is None else 值#解析引用占位
        except Exception:#识别失败
            return None#无

def _默认上下文(上下文id):#默认上下文
    """数字上下文。"""
    return None if 上下文id is None else {'kind':'numeric','id':上下文id}#数字上下文

def _原生上下文(上下文,数字键):#原生上下文参数
    """按种类构造上下文参数。"""
    if 上下文 is None:#无
        return None#无
    return {数字键:上下文['id']} if 上下文.get('kind')=='numeric' else {'uniqueContextId':上下文['id']}#按种类

def _转原生参数(值):#转原生参数
    """按种类转换调用参数。"""
    种类=值.get('kind')#种类
    if 种类=='value':#值
        return {'value':值['value']}#值
    if 种类=='unserializable':#不可序列化
        return {'unserializableValue':值['value']}#不可序列化
    if 种类=='object':#对象
        return {'objectId':值['handle']}#对象
    if 种类=='undefined':#undefined
        return {}#undefined
    raise RuntimeError(f'Unexpected Runtime call argument: {值!r}')#未预期
