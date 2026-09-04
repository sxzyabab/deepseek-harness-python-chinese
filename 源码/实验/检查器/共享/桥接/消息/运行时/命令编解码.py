"""Client Runtime 命令的精确线上解码器。

对齐上游 `shared/bridge/messages/runtime/command-codec.ts`。公开面仅中文名。
"""
from ....json import 是否json值,是否普通对象#JSON校验
from ....校验 import 精确键,可选布尔,可选非负数,可选字符串,线上标识#校验

__all__=['解析客户端运行时命令']#仅中文公开名

def 解析调用参数(值):#解析调用参数
    """解析调用参数。"""
    if not 是否普通对象(值) or not isinstance(值.get('kind'),str):#须有kind
        raise Exception('inspector protocol: invalid Client Runtime call argument')#英文诊断
    种类=值['kind']#种类
    if 种类=='value':#JSON值
        精确键(值,['kind','value'],'value call argument')#精确字段
        if not 是否json值(值['value']):#须JSON
            raise Exception('inspector protocol: call argument value must be JSON')#英文诊断
        return {'kind':'value','value':值['value']}#值参数
    if 种类=='unserializable':#不可序列化
        精确键(值,['kind','value'],'unserializable call argument')#精确字段
        if not isinstance(值['value'],str):#须字符串
            raise Exception('inspector protocol: unserializable argument must be a string')#英文诊断
        return {'kind':'unserializable','value':值['value']}#不可序列化参数
    if 种类=='object':#对象句柄
        精确键(值,['kind','handle'],'object call argument')#精确字段
        return {'kind':'object','handle':线上标识(值['handle'],'handle')}#对象参数
    if 种类=='undefined':#undefined
        精确键(值,['kind'],'undefined call argument')#精确字段
        return {'kind':'undefined'}#undefined参数
    raise Exception(f'inspector protocol: unknown call argument {种类!r}')#英文诊断

def 解析调用函数(值):#解析调用函数
    """解析调用函数。"""
    精确键(值,['op','functionDeclaration','receiver','arguments','objectGroup','silent','returnByValue','generatePreview','userGesture','awaitPromise'],'call-function command')#精确字段
    if not isinstance(值.get('functionDeclaration'),str):#函数声明非法
        raise Exception('inspector protocol: functionDeclaration must be a string')#英文诊断
    参数=None#可选参数列表
    if 值.get('arguments') is not None:#有参数
        if not isinstance(值['arguments'],list):#须数组
            raise Exception('inspector protocol: call arguments must be an array')#英文诊断
        参数=[解析调用参数(项) for 项 in 值['arguments']]#逐项解析
    结果={'op':'call-function','functionDeclaration':值['functionDeclaration']}#调用命令
    if 值.get('receiver') is not None:#可选接收者
        结果['receiver']=线上标识(值['receiver'],'receiver')#接收者句柄
    if 参数 is not None:#参数列表
        结果['arguments']=参数#参数列表
    结果.update(可选字符串(值,'objectGroup'))#对象组
    结果.update(可选布尔(值,'silent'))#静默
    结果.update(可选布尔(值,'returnByValue'))#按值返回
    结果.update(可选布尔(值,'generatePreview'))#生成预览
    结果.update(可选布尔(值,'userGesture'))#用户手势
    结果.update(可选布尔(值,'awaitPromise'))#等待Promise
    return 结果#返回结束

def 解析客户端运行时命令(值):#解析Runtime命令
    """在命令进入 Client 界域之前解析并重建一条 Runtime 命令。"""
    if not 是否普通对象(值) or not isinstance(值.get('op'),str):#须有op
        raise Exception('inspector protocol: Client Runtime command must have an op')#英文诊断
    操作=值['op']#操作
    if 操作=='evaluate':#求值
        精确键(值,['op','expression','objectGroup','includeCommandLineAPI','silent','returnByValue','generatePreview','userGesture','awaitPromise','disableBreaks','replMode','allowUnsafeEvalBlockedByCSP','timeoutMs'],'evaluate command')#精确字段
        if not isinstance(值.get('expression'),str):#须字符串
            raise Exception('inspector protocol: evaluate expression must be a string')#英文诊断
        结果={'op':'evaluate','expression':值['expression']}#求值命令
        结果.update(可选字符串(值,'objectGroup'))#对象组
        for 键 in ('includeCommandLineAPI','silent','returnByValue','generatePreview','userGesture','awaitPromise','disableBreaks','replMode','allowUnsafeEvalBlockedByCSP'):#可选布尔
            结果.update(可选布尔(值,键))#合并
        结果.update(可选非负数(值,'timeoutMs'))#超时
        return 结果#返回
    if 操作=='get-properties':#取属性
        精确键(值,['op','handle','ownProperties','accessorPropertiesOnly','generatePreview','nonIndexedPropertiesOnly'],'get-properties command')#精确字段
        结果={'op':'get-properties','handle':线上标识(值['handle'],'handle')}#取属性命令
        for 键 in ('ownProperties','accessorPropertiesOnly','generatePreview','nonIndexedPropertiesOnly'):#可选布尔
            结果.update(可选布尔(值,键))#合并
        return 结果#返回
    if 操作=='call-function':#调函数
        return 解析调用函数(值)#委托解析
    if 操作=='await-promise':#等Promise
        精确键(值,['op','promise','returnByValue','generatePreview'],'await-promise command')#精确字段
        结果={'op':'await-promise','promise':线上标识(值['promise'],'promise')}#等待命令
        结果.update(可选布尔(值,'returnByValue'))#按值返回
        结果.update(可选布尔(值,'generatePreview'))#生成预览
        return 结果#返回
    if 操作=='release-object':#释放对象
        精确键(值,['op','handle'],'release-object command')#精确字段
        return {'op':'release-object','handle':线上标识(值['handle'],'handle')}#释放命令
    if 操作=='release-object-group':#释放对象组
        精确键(值,['op','objectGroup'],'release-object-group command')#精确字段
        if not isinstance(值.get('objectGroup'),str):#须字符串
            raise Exception('inspector protocol: objectGroup must be a string')#英文诊断
        return {'op':'release-object-group','objectGroup':值['objectGroup']}#释放组命令
    if 操作=='global-lexical-scope-names':#全局词法名
        精确键(值,['op'],'global-lexical-scope-names command')#精确字段
        return {'op':'global-lexical-scope-names'}#词法名命令
    raise Exception(f'inspector protocol: unknown Client Runtime command {操作!r}')#英文诊断
