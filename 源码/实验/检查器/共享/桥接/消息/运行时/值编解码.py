"""Client Runtime 结果与 RemoteObject 数据的精确线上解码器。

对齐上游 `shared/bridge/messages/runtime/value-codec.ts`。公开面仅中文名。
"""
from ....json import 是否json值,是否普通对象#JSON校验
from ....校验 import 精确键,精确对象,可选布尔,可选字符串,线上标识#校验
from ....cordis.对象引用 import 解析检查器对象引用#对象引用
from ....cdp.远程对象 import 运行时远程对象类型,运行时远程对象子类型#类型常量

__all__=[#仅中文公开名
    '解析客户端运行时结果','解析客户端运行时远程对象',
    '解析客户端运行时异常详情','解析客户端运行时栈跟踪',
]#公开面结束

远程类型集合=set(运行时远程对象类型)#远程对象类型
远程子类型集合=set(运行时远程对象子类型)#远程对象子类型

def 要求表示(类型,有值,有不可序列化,有对象,期望值,期望不可序列化,期望对象):#要求表示形态
    """要求表示形态。"""
    if 有值!=期望值 or 有不可序列化!=期望不可序列化 or 有对象!=期望对象:#不匹配
        raise Exception(f'inspector protocol: invalid {类型} RemoteObject representation')#英文诊断

def 校验远程对象(值):#校验远程对象表示
    """校验远程对象表示。"""
    if 值.get('semanticReference') is not None and 值.get('object') is None:#语义引用须有对象
        raise Exception('inspector protocol: semanticReference requires a retained Client object')#英文诊断
    描述符=值['descriptor']#描述符
    if 描述符.get('subtype') is not None and 描述符.get('type')!='object':#仅object可有子类型
        raise Exception('inspector protocol: only object RemoteObjects may have a subtype')#英文诊断
    if 描述符.get('preview') is not None and 描述符.get('type')!='object':#仅object可有预览
        raise Exception('inspector protocol: only object RemoteObjects may have a preview')#英文诊断
    有值=描述符.get('value') is not None#是否有值
    有不可序列化=描述符.get('unserializableValue') is not None#是否有不可序列化
    有对象=值.get('object') is not None#是否有后端对象
    类型=描述符['type']#类型
    if 类型=='undefined':#undefined
        要求表示(类型,有值,有不可序列化,有对象,False,False,False)#无表示
        return#结束
    if 类型=='string':#字符串
        要求表示(类型,isinstance(描述符.get('value'),str),有不可序列化,有对象,True,False,False)#仅值
        return#结束
    if 类型=='boolean':#布尔
        要求表示(类型,isinstance(描述符.get('value'),bool),有不可序列化,有对象,True,False,False)#仅值
        return#结束
    if 类型=='number':#数字
        数=描述符.get('value')#值
        有限=isinstance(数,(int,float)) and not isinstance(数,bool) and 数==数 and 数 not in (float('inf'),float('-inf'))#有限
        特殊=描述符.get('unserializableValue') in ('NaN','Infinity','-Infinity','-0')#特殊字面量
        if 有对象 or 有限==特殊:#恰一表示
            raise Exception('inspector protocol: invalid number RemoteObject representation')#英文诊断
        return#结束
    if 类型=='bigint':#大整数
        import re#字面量
        if 有值 or 有对象 or not re.fullmatch(r'-?(?:0|[1-9]\d*)n',描述符.get('unserializableValue') or ''):#须不可序列化
            raise Exception('inspector protocol: invalid bigint RemoteObject representation')#英文诊断
        return#结束
    if 类型 in ('symbol','function'):#符号或函数
        要求表示(类型,有值,有不可序列化,有对象,False,False,True)#仅对象
        return#结束
    if 类型=='object':#对象
        if 描述符.get('subtype')=='null':#null子类型
            if 描述符.get('value') is not None or 有对象 or 有不可序列化:#须值为null —— TS要求 value===null
                if 描述符.get('value') is not None or 有对象 or 有不可序列化:#非法
                    if not (描述符.get('value') is None and not 有对象 and not 有不可序列化 and 'value' in 描述符):#须显式null
                        if 描述符.get('value') is not None or 有对象 or 有不可序列化:#仍非法
                            pass#落下方
            if 描述符.get('value') is not None or 有对象 or 有不可序列化:#非法表示
                if not (描述符.get('value') is None and 'value' in 描述符 and not 有对象 and not 有不可序列化):#非合法null
                    raise Exception('inspector protocol: invalid null RemoteObject representation')#英文诊断
            return#结束
        if 有不可序列化 or 有值==有对象:#恰一值或对象
            raise Exception('inspector protocol: object RemoteObject needs exactly one value or backend object')#英文诊断

def 解析属性预览(值):#解析属性预览
    """解析属性预览。"""
    记录=精确对象(值,['name','type','value','valuePreview','subtype'],'property preview')#精确对象
    if not isinstance(记录.get('name'),str) or (记录.get('type')!='accessor' and 记录.get('type') not in 远程类型集合) or (记录.get('subtype') is not None and 记录.get('subtype') not in 远程子类型集合):#非法
        raise Exception('inspector protocol: invalid property preview')#英文诊断
    结果={'name':记录['name'],'type':记录['type']}#属性预览
    结果.update(可选字符串(记录,'value'))#展示值
    if 记录.get('valuePreview') is not None:#嵌套预览
        结果['valuePreview']=解析对象预览(记录['valuePreview'])#嵌套预览
    if 记录.get('subtype') is not None:#子类型
        结果['subtype']=记录['subtype']#子类型
    return 结果#返回

def 解析对象预览(值):#解析对象预览
    """解析对象预览。"""
    记录=精确对象(值,['type','subtype','description','overflow','properties'],'object preview')#精确对象
    if 记录.get('type') not in 远程类型集合 or (记录.get('subtype') is not None and 记录.get('subtype') not in 远程子类型集合) or not isinstance(记录.get('overflow'),bool) or not isinstance(记录.get('properties'),list):#非法
        raise Exception('inspector protocol: invalid object preview')#英文诊断
    结果={'type':记录['type'],'overflow':记录['overflow'],'properties':[解析属性预览(项) for 项 in 记录['properties']]}#对象预览
    if 记录.get('subtype') is not None:#子类型
        结果['subtype']=记录['subtype']#子类型
    结果.update(可选字符串(记录,'description'))#描述
    return 结果#返回

def 解析远程对象描述符(值):#解析远程对象描述符
    """解析远程对象描述符。"""
    记录=精确对象(值,['type','subtype','className','value','unserializableValue','description','preview'],'Runtime object descriptor')#精确对象
    if 记录.get('type') not in 远程类型集合:#类型非法
        raise Exception('inspector protocol: invalid Client RemoteObject type')#英文诊断
    if 记录.get('subtype') is not None and 记录.get('subtype') not in 远程子类型集合:#子类型非法
        raise Exception('inspector protocol: invalid Client RemoteObject subtype')#英文诊断
    if 记录.get('value') is not None and not 是否json值(记录['value']):#值须JSON
        raise Exception('inspector protocol: Client RemoteObject value must be JSON')#英文诊断
    结果={'type':记录['type']}#描述符
    if 记录.get('subtype') is not None:#子类型
        结果['subtype']=记录['subtype']#子类型
    结果.update(可选字符串(记录,'className'))#类名
    if 记录.get('value') is not None or ('value' in 记录 and 记录['value'] is None and 记录.get('subtype')=='null'):#可序列化值
        if 'value' in 记录:#有value键
            结果['value']=记录['value']#值
    结果.update(可选字符串(记录,'unserializableValue'))#不可序列化
    结果.update(可选字符串(记录,'description'))#描述
    if 记录.get('preview') is not None:#预览
        结果['preview']=解析对象预览(记录['preview'])#预览
    return 结果#返回

def 解析客户端运行时远程对象(值):#解析远程对象
    """解码一个携带可选会话本地句柄的 Client Runtime 对象。"""
    记录=精确对象(值,['descriptor','object','semanticReference'],'Client Runtime object')#精确对象
    描述符=解析远程对象描述符(记录['descriptor'])#描述符
    对象=None if 记录.get('object') is None else 精确对象(记录['object'],['handle'],'Client Runtime object reference')#引用对象
    远程={'descriptor':描述符}#远程对象
    if 对象 is not None:#可选句柄
        远程['object']={'handle':线上标识(对象['handle'],'handle')}#后端引用
    if 记录.get('semanticReference') is not None:#可选语义引用
        远程['semanticReference']=解析检查器对象引用(记录['semanticReference'])#Cordis引用
    校验远程对象(远程)#校验表示
    return 远程#远程对象

def 解析调用帧(值):#解析调用帧
    """解析调用帧。"""
    记录=精确对象(值,['functionName','scriptKey','url','lineNumber','columnNumber'],'stack call frame')#精确对象
    if not isinstance(记录.get('functionName'),str) or not isinstance(记录.get('url'),str) or not isinstance(记录.get('lineNumber'),int) or isinstance(记录.get('lineNumber'),bool) or not isinstance(记录.get('columnNumber'),int) or isinstance(记录.get('columnNumber'),bool):#非法
        raise Exception('inspector protocol: invalid stack call frame')#英文诊断
    结果={'functionName':记录['functionName'],'url':记录['url'],'lineNumber':记录['lineNumber'],'columnNumber':记录['columnNumber']}#调用帧
    if 记录.get('scriptKey') is not None:#脚本键
        结果['scriptKey']=线上标识(记录['scriptKey'],'scriptKey')#脚本键
    return 结果#返回

def 解析客户端运行时栈跟踪(值):#解析栈跟踪
    """解码 Client Runtime 或 Console 帧携带的栈追踪。"""
    记录=精确对象(值,['description','callFrames','parent'],'stack trace')#精确对象
    if not isinstance(记录.get('callFrames'),list):#须数组
        raise Exception('inspector protocol: stack callFrames must be an array')#英文诊断
    结果={'callFrames':[解析调用帧(项) for 项 in 记录['callFrames']]}#栈跟踪
    结果.update(可选字符串(记录,'description'))#描述
    if 记录.get('parent') is not None:#父栈
        结果['parent']=解析客户端运行时栈跟踪(记录['parent'])#父栈
    return 结果#返回

def 解析客户端运行时异常详情(值):#解析异常详情
    """解码命令结果与事件所用的 Client 异常详情。"""
    记录=精确对象(值,['text','lineNumber','columnNumber','url','stackTrace','exception'],'exception details')#精确对象
    if not isinstance(记录.get('text'),str) or not isinstance(记录.get('lineNumber'),int) or isinstance(记录.get('lineNumber'),bool) or 记录['lineNumber']<0 or not isinstance(记录.get('columnNumber'),int) or isinstance(记录.get('columnNumber'),bool) or 记录['columnNumber']<0:#非法
        raise Exception('inspector protocol: invalid exception details')#英文诊断
    结果={'text':记录['text'],'lineNumber':记录['lineNumber'],'columnNumber':记录['columnNumber']}#异常详情
    结果.update(可选字符串(记录,'url'))#URL
    if 记录.get('stackTrace') is not None:#栈
        结果['stackTrace']=解析客户端运行时栈跟踪(记录['stackTrace'])#栈
    if 记录.get('exception') is not None:#异常对象
        结果['exception']=解析客户端运行时远程对象(记录['exception'])#异常对象
    return 结果#返回

def 解析属性描述符(值):#解析属性描述符
    """解析属性描述符。"""
    记录=精确对象(值,['name','value','writable','get','set','configurable','enumerable','wasThrown','isOwn','symbol'],'property descriptor')#精确对象
    if not isinstance(记录.get('name'),str) or not isinstance(记录.get('configurable'),bool) or not isinstance(记录.get('enumerable'),bool):#形状非法
        raise Exception('inspector protocol: invalid property descriptor')#英文诊断
    数据=记录.get('value') is not None or 记录.get('writable') is not None#数据描述符
    访问器=记录.get('get') is not None or 记录.get('set') is not None#访问器描述符
    if 数据 and 访问器:#混用非法
        raise Exception('inspector protocol: property descriptor mixes data and accessor fields')#英文诊断
    结果={'name':记录['name'],'configurable':记录['configurable'],'enumerable':记录['enumerable']}#属性描述符
    if 记录.get('value') is not None:#数据值
        结果['value']=解析客户端运行时远程对象(记录['value'])#数据值
    结果.update(可选布尔(记录,'writable'))#可写
    if 记录.get('get') is not None:#getter
        结果['get']=解析客户端运行时远程对象(记录['get'])#getter
    if 记录.get('set') is not None:#setter
        结果['set']=解析客户端运行时远程对象(记录['set'])#setter
    结果.update(可选布尔(记录,'wasThrown'))#读取抛错
    结果.update(可选布尔(记录,'isOwn'))#是否自有
    if 记录.get('symbol') is not None:#符号键
        结果['symbol']=解析客户端运行时远程对象(记录['symbol'])#符号键
    return 结果#返回

def 解析内部属性描述符(值):#解析内部属性
    """解析内部属性。"""
    记录=精确对象(值,['name','value'],'internal property descriptor')#精确对象
    if not isinstance(记录.get('name'),str):#名须字符串
        raise Exception('inspector protocol: invalid internal property descriptor')#英文诊断
    结果={'name':记录['name']}#内部属性
    if 记录.get('value') is not None:#值
        结果['value']=解析客户端运行时远程对象(记录['value'])#值
    return 结果#返回

def 解析完成(值):#解析完成结果
    """解析完成结果。"""
    记录=精确对象(值,['result','exceptionDetails'],'Client Runtime completion')#精确对象
    结果={'result':解析客户端运行时远程对象(记录['result'])}#完成结果
    if 记录.get('exceptionDetails') is not None:#可选异常
        结果['exceptionDetails']=解析客户端运行时异常详情(记录['exceptionDetails'])#异常详情
    return 结果#返回

def 解析客户端运行时结果(值):#解析Runtime结果
    """解析并重建一次成功的 Client Runtime 结果。"""
    if not 是否普通对象(值) or not isinstance(值.get('op'),str):#须有op
        raise Exception('inspector protocol: Client Runtime result must have an op')#英文诊断
    操作=值['op']#操作
    if 操作 in ('evaluate','call-function','await-promise'):#完成类
        精确键(值,['op','completion'],f'{操作} result')#精确字段
        return {'op':操作,'completion':解析完成(值['completion'])}#完成结果
    if 操作=='get-properties':#取属性
        精确键(值,['op','properties','internalProperties','exceptionDetails'],'get-properties result')#精确字段
        if not isinstance(值.get('properties'),list):#须数组
            raise Exception('inspector protocol: properties must be an array')#英文诊断
        内部=值.get('internalProperties')#内部属性
        if 内部 is not None and not isinstance(内部,list):#内部须数组
            raise Exception('inspector protocol: internalProperties must be an array')#英文诊断
        结果={'op':'get-properties','properties':[解析属性描述符(项) for 项 in 值['properties']]}#取属性结果
        if 内部 is not None:#内部属性
            结果['internalProperties']=[解析内部属性描述符(项) for 项 in 内部]#内部属性
        if 值.get('exceptionDetails') is not None:#可选异常
            结果['exceptionDetails']=解析客户端运行时异常详情(值['exceptionDetails'])#异常详情
        return 结果#返回
    if 操作 in ('release-object','release-object-group'):#空结果
        精确键(值,['op'],f'{操作} result')#精确字段
        return {'op':操作}#空结果
    if 操作=='global-lexical-scope-names':#词法名
        精确键(值,['op','names'],'global-lexical-scope-names result')#精确字段
        if not isinstance(值.get('names'),list) or not all(isinstance(名,str) for 名 in 值['names']):#须字符串数组
            raise Exception('inspector protocol: lexical scope names must be strings')#英文诊断
        return {'op':'global-lexical-scope-names','names':值['names']}#词法名结果
    raise Exception(f'inspector protocol: unknown Client Runtime result {操作!r}')#英文诊断
