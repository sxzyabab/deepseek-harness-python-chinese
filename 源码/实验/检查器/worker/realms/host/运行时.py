from ......基础设施.js特性 import PromiseEX as 期约扩展#后端方法的返回期约
from ....异常 import 检查器错误#包内错误
from .值 import 是否原生记录,可选原生字段,要求原生记录#值工具
from .脚本 import Host脚本键#脚本键

__all__=['Host运行时后端']#仅中文公开名

class Host运行时后端:#Host Runtime后端
    '在公共值背后保留原生 V8 语义的 Host Runtime 适配器'
    def __init__(自身,目标):#构造
        '观察上下文'
        自身.目标=目标#会话
        自身._默认上下文id=None#默认上下文id
        自身._取消订阅=目标.订阅(自身._观察上下文)#观察上下文

    def 启用(自身):#启用
        'Runtime.enable，返回期约'
        return 自身.目标.请求('Runtime.enable',{})#请求

    def 禁用(自身):#禁用
        'Runtime.disable，返回期约，禁用完成后才清空默认上下文'
        def 清空默认上下文(结果):#禁用请求完成后调用
            '清空默认上下文并原样传递结果'
            自身._默认上下文id=None#清空默认
            return 结果#传递结果
        return 自身.目标.请求('Runtime.disable',{}).然后(清空默认上下文)#请求完成后再清空

    def 求值(自身,请求):#求值
        'Runtime.evaluate，返回期约'
        原生=_原生上下文(请求['context'] if 'context' in 请求 else None,'contextId')#原生上下文或 None
        return 自身.目标.请求('Runtime.evaluate',{#请求
            'expression':请求['expression'],#表达式
            **({} if 原生 is None else 原生),#上下文，None 才空表
            **可选原生字段('objectGroup',请求['objectGroup'] if 'objectGroup' in 请求 else None),#对象组
            **可选原生字段('includeCommandLineAPI',请求['includeCommandLineAPI'] if 'includeCommandLineAPI' in 请求 else None),#命令行API
            **可选原生字段('silent',请求['silent'] if 'silent' in 请求 else None),#静默
            **可选原生字段('returnByValue',请求['returnByValue'] if 'returnByValue' in 请求 else None),#按值
            **可选原生字段('generatePreview',请求['generatePreview'] if 'generatePreview' in 请求 else None),#预览
            **可选原生字段('userGesture',请求['userGesture'] if 'userGesture' in 请求 else None),#手势
            **可选原生字段('awaitPromise',请求['awaitPromise'] if 'awaitPromise' in 请求 else None),#等Promise
            **可选原生字段('disableBreaks',请求['disableBreaks'] if 'disableBreaks' in 请求 else None),#禁用断点
            **可选原生字段('replMode',请求['replMode'] if 'replMode' in 请求 else None),#REPL
            **可选原生字段('allowUnsafeEvalBlockedByCSP',请求['allowUnsafeEvalBlockedByCSP'] if 'allowUnsafeEvalBlockedByCSP' in 请求 else None),#CSP
            **可选原生字段('throwOnSideEffect',请求['throwOnSideEffect'] if 'throwOnSideEffect' in 请求 else None),#副作用
            **可选原生字段('serializationOptions',请求['serializationOptions'] if 'serializationOptions' in 请求 else None),#序列化
            **可选原生字段('timeout',请求['timeoutMs'] if 'timeoutMs' in 请求 else None),#超时
        }).然后(自身.完成)#请求完成后再转换

    def 取属性(自身,请求):#取属性
        'Runtime.getProperties，返回期约'
        return 自身.目标.请求('Runtime.getProperties',{#请求
            'objectId':请求['handle'],#对象id
            **可选原生字段('ownProperties',请求['ownProperties'] if 'ownProperties' in 请求 else None),#自有
            **可选原生字段('accessorPropertiesOnly',请求['accessorPropertiesOnly'] if 'accessorPropertiesOnly' in 请求 else None),#仅访问器
            **可选原生字段('generatePreview',请求['generatePreview'] if 'generatePreview' in 请求 else None),#预览
            **可选原生字段('nonIndexedPropertiesOnly',请求['nonIndexedPropertiesOnly'] if 'nonIndexedPropertiesOnly' in 请求 else None),#非索引
        }).然后(自身._属性集)#请求完成后再转换

    def 调函数(自身,请求):#调函数
        'Runtime.callFunctionOn，返回期约'
        接收者=请求['receiver'] if 'receiver' in 请求 else None#接收者
        if 接收者 is not None:#有接收者
            上下文=None#不附上下文
        else:#无接收者
            所选=请求['context'] if 'context' in 请求 and 请求['context'] is not None else _默认上下文(自身._默认上下文id)#所选上下文
            上下文=_原生上下文(所选,'executionContextId')#上下文
        if 接收者 is None and 上下文 is None:#不可用
            raise 检查器错误('Host Runtime 默认执行上下文不可用')#抛错
        参数={#请求
            'functionDeclaration':请求['functionDeclaration'],#函数声明
            **({'objectId':接收者} if 接收者 is not None else 上下文),#目标
            **可选原生字段('objectGroup',请求['objectGroup'] if 'objectGroup' in 请求 else None),#对象组
            **可选原生字段('silent',请求['silent'] if 'silent' in 请求 else None),#静默
            **可选原生字段('returnByValue',请求['returnByValue'] if 'returnByValue' in 请求 else None),#按值
            **可选原生字段('generatePreview',请求['generatePreview'] if 'generatePreview' in 请求 else None),#预览
            **可选原生字段('userGesture',请求['userGesture'] if 'userGesture' in 请求 else None),#手势
            **可选原生字段('awaitPromise',请求['awaitPromise'] if 'awaitPromise' in 请求 else None),#等Promise
            **可选原生字段('throwOnSideEffect',请求['throwOnSideEffect'] if 'throwOnSideEffect' in 请求 else None),#副作用
            **可选原生字段('serializationOptions',请求['serializationOptions'] if 'serializationOptions' in 请求 else None),#序列化
        }#参数结束
        if 'arguments' in 请求 and 请求['arguments'] is not None:#有参数
            参数['arguments']=[_转原生参数(项) for 项 in 请求['arguments']]#参数
        return 自身.目标.请求('Runtime.callFunctionOn',参数).然后(自身.完成)#请求完成后再转换

    def 等Promise(自身,请求):#等Promise
        'Runtime.awaitPromise，返回期约'
        return 自身.目标.请求('Runtime.awaitPromise',{#请求
            'promiseObjectId':请求['promise'],#Promise id
            **可选原生字段('returnByValue',请求['returnByValue'] if 'returnByValue' in 请求 else None),#按值
            **可选原生字段('generatePreview',请求['generatePreview'] if 'generatePreview' in 请求 else None),#预览
        }).然后(自身.完成)#请求完成后再转换

    def 全局词法名(自身,上下文=None):#全局词法名
        'Runtime.globalLexicalScopeNames，返回期约，兑现值是名字列表'
        所选=上下文 if 上下文 is not None else _默认上下文(自身._默认上下文id)#所选上下文
        原生=_原生上下文(所选,'executionContextId')#原生上下文或 None
        def 校验名字(响应):#请求完成后调用
            '校验并取出名字列表'
            名字=响应['names'] if 'names' in 响应 else None#名字
            if not isinstance(名字,list) or not all(isinstance(名,str) for 名 in 名字):#校验
                raise 检查器错误('Host Runtime 返回了无效的词法作用域名')#无效
            return 名字#名字
        return 自身.目标.请求('Runtime.globalLexicalScopeNames',{#请求
            **({} if 原生 is None else 原生),#上下文，None 才空表
        }).然后(校验名字)#请求完成后再校验

    def 释放对象(自身,句柄):#释放对象
        'Runtime.releaseObject，返回期约'
        return 自身.目标.请求('Runtime.releaseObject',{'objectId':句柄})#请求

    def 释放对象组(自身,组):#释放对象组
        'Runtime.releaseObjectGroup，返回期约'
        return 自身.目标.请求('Runtime.releaseObjectGroup',{'objectGroup':组})#请求

    def 关闭(自身):#关闭
        '拆除本后端拥有的原生上下文观察者'
        自身._取消订阅()#取消订阅

    def 完成(自身,值):#完成
        '转换原生 Runtime 完成，返回期约'
        def 加入异常详情(结果):#结果对象转换完成后调用
            '有异常详情时再转换异常详情'
            输出={'result':结果}#结果
            if 'exceptionDetails' not in 值 or 值['exceptionDetails'] is None:#无异常
                return 输出#直接返回
            def 写入异常详情(详情):#异常详情转换完成后调用
                '写入输出'
                输出['exceptionDetails']=详情#含异常
                return 输出#返回
            return 自身.异常详情(值['exceptionDetails']).然后(写入异常详情)#异常详情转换完成后再写入
        return 自身.远程对象(值['result'] if 'result' in 值 else None).然后(加入异常详情)#结果对象转换完成后再继续

    def _属性集(自身,值):#属性集
        '转换属性结果，返回期约'
        if 'result' not in 值 or not isinstance(值['result'],list):#无效
            raise 检查器错误('Host Runtime 返回了无效的属性')#无效
        分项名=['properties']#输出里各分项的键，顺序与期约列表一致
        分项期约=[期约扩展.全部([自身._属性(项) for 项 in 值['result']])]#各属性并发转换
        if 'internalProperties' in 值 and 值['internalProperties'] is not None:#内部
            分项名.append('internalProperties')#内部属性键
            分项期约.append(自身._内部属性(值['internalProperties']))#内部属性转换
        if 'privateProperties' in 值 and 值['privateProperties'] is not None:#私有
            分项名.append('privateProperties')#私有属性键
            分项期约.append(自身._私有属性(值['privateProperties']))#私有属性转换
        if 'exceptionDetails' in 值 and 值['exceptionDetails'] is not None:#异常
            分项名.append('exceptionDetails')#异常详情键
            分项期约.append(自身.异常详情(值['exceptionDetails']))#异常详情转换
        def 组装输出(分项结果):#各分项转换完成后调用
            '按分项键组装输出'
            return dict(zip(分项名,分项结果))#键与结果一一对应
        return 期约扩展.全部(分项期约).然后(组装输出)#各分项都完成后再组装

    def _属性(自身,值):#属性描述符
        '转换属性描述符，返回期约'
        记录=要求原生记录(值,'Host Runtime property descriptor')#记录
        if not isinstance(记录.get('name'),str) or not isinstance(记录.get('configurable'),bool) or not isinstance(记录.get('enumerable'),bool):#无效
            raise 检查器错误('Host Runtime 返回了无效的属性描述符')#无效
        描述符={**记录,'name':记录['name'],'configurable':记录['configurable'],'enumerable':记录['enumerable']}#描述符
        return 自身.填充远程对象(描述符,记录,('value','get','set','symbol'))#值、getter、setter、符号转成远程对象

    def _内部属性(自身,值):#内部属性
        '转换内部属性列表，返回期约'
        if not isinstance(值,list):#无效
            raise 检查器错误('Host Runtime 返回了无效的内部属性')#无效
        def 转换内部属性项(项):#逐项转换
            '校验一项并把 value 转成远程对象'
            记录=要求原生记录(项,'Host Runtime internal property')#记录
            if not isinstance(记录.get('name'),str):#无效
                raise 检查器错误('Host Runtime 返回了无效的内部属性')#无效
            return 自身.填充远程对象({'name':记录['name']},记录,('value',))#值转成远程对象
        return 期约扩展.全部([转换内部属性项(项) for 项 in 值])#各项并发转换

    def _私有属性(自身,值):#私有属性
        '转换私有属性列表，返回期约'
        if not isinstance(值,list):#无效
            raise 检查器错误('Host Runtime 返回了无效的私有属性')#无效
        def 转换私有属性项(项):#逐项转换
            '校验一项并把 value、get、set 转成远程对象'
            记录=要求原生记录(项,'Host Runtime private property')#记录
            if not isinstance(记录.get('name'),str):#无效
                raise 检查器错误('Host Runtime 返回了无效的私有属性')#无效
            return 自身.填充远程对象({'name':记录['name']},记录,('value','get','set'))#值、getter、setter转成远程对象
        return 期约扩展.全部([转换私有属性项(项) for 项 in 值])#各项并发转换

    def 填充远程对象(自身,描述符,记录,键元组):#填充远程对象字段
        '把记录里存在且非空的键转成远程对象写进描述符，返回期约，兑现值是描述符'
        待转换键=[键 for 键 in 键元组 if 键 in 记录 and 记录[键] is not None]#实际存在的键
        def 写入远程对象(远程对象列表):#全部转换完成后调用
            '按键顺序写回描述符'
            for 键,远程 in zip(待转换键,远程对象列表):#键与远程对象一一对应
                描述符[键]=远程#写入
            return 描述符#返回
        return 期约扩展.全部([自身.远程对象(记录[键]) for 键 in 待转换键]).然后(写入远程对象)#全部转换完成后再写入

    def 异常详情(自身,值):#异常详情
        '转换原生异常详情，返回期约'
        记录=要求原生记录(值,'Host Runtime exception details')#记录
        行号=记录['lineNumber'] if 'lineNumber' in 记录 else None#行号
        列号=记录['columnNumber'] if 'columnNumber' in 记录 else None#列号
        if not isinstance(记录.get('text'),str) or not isinstance(行号,int) or isinstance(行号,bool) or not isinstance(列号,int) or isinstance(列号,bool):#无效
            raise 检查器错误('Host Runtime 返回了无效的异常详情')#无效
        详情={**记录,'text':记录['text'],'lineNumber':行号,'columnNumber':列号}#详情
        if 'stackTrace' in 记录 and 记录['stackTrace'] is not None:#栈
            详情['stackTrace']=自身.栈跟踪(记录['stackTrace'])#栈
        return 自身.填充远程对象(详情,记录,('exception',))#异常对象转成远程对象

    def 远程对象(自身,值):#远程对象
        '转换原生 V8 RemoteObject，返回期约'
        记录=要求原生记录(值,'Host Runtime RemoteObject')#记录
        if not isinstance(记录.get('type'),str):#无效
            raise 检查器错误('Host Runtime 返回了无效的 RemoteObject')#无效
        描述符={键:项 for 键,项 in 记录.items() if 键!='objectId'}#去掉objectId
        对象id=记录['objectId'] if isinstance(记录.get('objectId'),str) else None#对象id
        def 组装远程对象(语义):#语义识别完成后调用
            '组装公共远程对象'
            输出={'descriptor':描述符}#远程对象
            if 对象id is not None:#句柄
                输出['object']={'handle':对象id}#句柄
            if 语义 is not None:#语义
                输出['semanticReference']=语义#语义
            return 输出#返回
        return 自身._识别对象(对象id).然后(组装远程对象)#语义识别完成后再组装

    def 栈跟踪(自身,值):#栈跟踪
        '转换原生栈跟踪'
        记录=要求原生记录(值,'Host Runtime stack trace')#记录
        if 'callFrames' not in 记录 or not isinstance(记录['callFrames'],list):#无效
            raise 检查器错误('Host Runtime 返回了无效的栈跟踪')#无效
        帧列表=[]#帧
        for 帧 in 记录['callFrames']:#帧
            字段=要求原生记录(帧,'Host Runtime call frame')#字段
            行号=字段['lineNumber'] if 'lineNumber' in 字段 else None#行号
            列号=字段['columnNumber'] if 'columnNumber' in 字段 else None#列号
            if not isinstance(字段.get('functionName'),str) or not isinstance(字段.get('url'),str) or not isinstance(行号,int) or isinstance(行号,bool) or not isinstance(列号,int) or isinstance(列号,bool):#无效
                raise 检查器错误('Host Runtime 返回了无效的调用帧')#无效
            项={'functionName':字段['functionName'],'url':字段['url'],'lineNumber':行号,'columnNumber':列号}#帧对象
            if isinstance(字段.get('scriptId'),str):#脚本
                项['scriptKey']=Host脚本键(字段['scriptId'])#键
            帧列表.append(项)#收集
        栈={'callFrames':帧列表}#栈
        if isinstance(记录.get('description'),str):#描述
            栈['description']=记录['description']#描述
        if 'parent' in 记录 and 记录['parent'] is not None:#父栈
            栈['parent']=自身.栈跟踪(记录['parent'])#父栈
        return 栈#返回

    def _观察上下文(自身,消息):#观察上下文
        '跟踪默认执行上下文'
        if 消息.get('method')=='Runtime.executionContextCreated':#创建
            参数=消息['params'] if 'params' in 消息 else None#参数
            上下文=参数['context'] if isinstance(参数,dict) and 'context' in 参数 else None#上下文
            上下文=上下文 if 是否原生记录(上下文) else None#上下文
            辅助=上下文['auxData'] if 上下文 is not None and 'auxData' in 上下文 else None#辅助
            辅助=辅助 if 是否原生记录(辅助) else None#辅助
            上下文id=上下文['id'] if 上下文 is not None and 'id' in 上下文 else None#上下文id
            if 上下文 is not None and 辅助 is not None and 辅助.get('isDefault') is True and isinstance(上下文id,int) and not isinstance(上下文id,bool):#默认
                自身._默认上下文id=上下文id#保存
            return#返回
        if 消息.get('method')!='Runtime.executionContextDestroyed':#非销毁
            return#返回
        参数=消息['params'] if 'params' in 消息 else None#参数
        if isinstance(参数,dict) and 参数.get('executionContextId')==自身._默认上下文id:#清空
            自身._默认上下文id=None#清空

    def _识别对象(自身,对象id):#识别对象
        '可选语义识别，返回期约，兑现值是语义引用或 None，识别失败也兑现 None'
        if 对象id is None:#无对象句柄，无需识别
            无对象=期约扩展()#空结果期约
            无对象.解决(None)#没有语义引用
            return 无对象#返回已解决的期约
        def 解析引用(响应):#识别请求完成后调用
            '取出语义引用'
            if ('exceptionDetails' in 响应 and 响应['exceptionDetails'] is not None) or not 是否原生记录(响应['result'] if 'result' in 响应 else None):#失败
                return None#无
            return 响应['result']['value'] if 'value' in 响应['result'] else None#解析引用占位
        def 忽略识别失败(错误):#识别请求被拒绝后调用
            '语义识别是可选元数据，失败时保留 Runtime 值'
            return None#无
        return 自身.目标.请求('Runtime.callFunctionOn',{#调用识别函数
            'objectId':对象id,#对象
            'functionDeclaration':'function(){return this&&this.__dshObjectReference||null}',#识别函数占位
            'returnByValue':True,'silent':True,#静默
        }).然后(解析引用,忽略识别失败)#请求完成后再解析

def _默认上下文(上下文id):#默认上下文
    '数字上下文'
    return None if 上下文id is None else {'kind':'numeric','id':上下文id}#数字上下文

def _原生上下文(上下文,数字键):#原生上下文参数
    '按种类构造上下文参数'
    if 上下文 is None:#无
        return None#无
    return {数字键:上下文['id']} if 上下文.get('kind')=='numeric' else {'uniqueContextId':上下文['id']}#按种类

def _转原生参数(值):#转原生参数
    '按种类转换调用参数'
    种类=值['kind']#种类
    if 种类=='value':#值
        return {'value':值['value']}#值
    if 种类=='unserializable':#不可序列化
        return {'unserializableValue':值['value']}#不可序列化
    if 种类=='object':#对象
        return {'objectId':值['handle']}#对象
    if 种类=='undefined':#undefined
        return {}#undefined
    raise 检查器错误(f'未预期的 Runtime 调用参数：{值!r}')#未预期
