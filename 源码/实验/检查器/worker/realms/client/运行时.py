"""类型化 Worker→Client 传输上的 RuntimeBackend。"""
#对齐上游 worker/realms/client/runtime.ts

from ......内核.智能体循环.辅助 import 解开,操作任务#可等待则等待|单次结果
from .值 import Client完成,Client异常,Client句柄,Client属性,Client内部属性#值转换

__all__=['Client运行时后端']#仅中文公开名

class Client运行时后端:#Client Runtime后端
    """将一个连接本地 Client Runtime 会话适配到公共后端 API。"""
    def __init__(自身,目标,会话id,路由,脚本身份):#构造
        """保存依赖。"""
        自身.目标=目标#目标
        自身.会话id=会话id#会话
        自身.路由=路由#路由
        自身.脚本身份=脚本身份#脚本身份
        自身._已关闭=False#是否已关闭

    def 启用(自身):#启用
        """无操作。"""
        return#无操作

    def 禁用(自身):#禁用
        """关闭目标会话。"""
        自身.路由.关闭目标会话(自身.目标,自身.会话id)#关会话

    def 求值(自身,请求):#求值
        """执行 evaluate。"""
        _断言求值选项(请求)#断言选项
        支持={键:值 for 键,值 in 请求.items() if 键 not in ('context','throwOnSideEffect','serializationOptions')}#支持的
        return Client完成(自身._期望(解开(自身._请求({'op':'evaluate',**支持})),'evaluate'),自身.脚本身份.转Runtime)#转换

    def 取属性(自身,请求):#取属性
        """执行 get-properties。"""
        结果=自身._期望(解开(自身._请求({'op':'get-properties',**请求,'handle':Client句柄(请求['handle'])})),'get-properties')#请求
        输出={'properties':[Client属性(项) for 项 in 结果['properties']]}#属性
        if 'internalProperties' in 结果:#内部属性
            输出['internalProperties']=[Client内部属性(项) for 项 in 结果['internalProperties']]#映射
        if 'exceptionDetails' in 结果:#异常
            输出['exceptionDetails']=Client异常(结果['exceptionDetails'],自身.脚本身份.转Runtime)#转换
        return 输出#返回

    def 调函数(自身,请求):#调函数
        """执行 call-function。"""
        _断言调用选项(请求)#断言选项
        接收者=请求.get('receiver')#接收者
        参数列表=请求.get('arguments')#参数
        选项={键:值 for 键,值 in 请求.items() if 键 not in ('receiver','context','arguments','throwOnSideEffect','serializationOptions')}#其余
        命令={'op':'call-function',**选项}#命令
        if 接收者 is not None:#有接收者
            命令['receiver']=Client句柄(接收者)#接收者
        if 参数列表 is not None:#有参数
            命令['arguments']=[_参数转Client(项) for 项 in 参数列表]#参数
        return Client完成(自身._期望(解开(自身._请求(命令)),'call-function'),自身.脚本身份.转Runtime)#转换

    def 等Promise(自身,请求):#等Promise
        """执行 await-promise。"""
        return Client完成(自身._期望(解开(自身._请求({'op':'await-promise',**请求,'promise':Client句柄(请求['promise'])})),'await-promise'),自身.脚本身份.转Runtime)#转换

    def 全局词法名(自身,上下文=None):#全局词法名
        """执行 global-lexical-scope-names。"""
        if 上下文 is not None:#不支持上下文
            raise RuntimeError('Client Runtime does not support native execution contexts')#抛错
        return 自身._期望(解开(自身._请求({'op':'global-lexical-scope-names'})),'global-lexical-scope-names')['names']#名字

    def 释放对象(自身,句柄):#释放对象
        """执行 release-object。"""
        自身._期望(解开(自身._请求({'op':'release-object','handle':Client句柄(句柄)})),'release-object')#请求

    def 释放对象组(自身,组):#释放对象组
        """执行 release-object-group。"""
        自身._期望(解开(自身._请求({'op':'release-object-group','objectGroup':组})),'release-object-group')#请求

    def 关闭(自身):#关闭
        """关闭本连接的会话并拒绝后续请求。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身.路由.关闭目标会话(自身.目标,自身.会话id)#关会话

    def _请求(自身,命令):#发起请求
        """路由请求。"""
        if 自身._已关闭:#已关闭
            任务=操作任务()#失败任务
            任务.拒绝(RuntimeError('Client realm session is closed'))#拒绝
            return 任务#返回
        return 自身.路由.请求(自身.目标,自身.会话id,命令)#路由

    def _期望(自身,结果,操作):#期望结果
        """窄化结果操作。"""
        结果=解开(结果)#可等待则等待
        if 结果.get('op')!=操作:#不符
            raise RuntimeError(f"Client Runtime returned {结果.get('op')} for {操作}")#抛错
        return 结果#返回

def _参数转Client(值):#参数转Client
    """对象改句柄。"""
    return {'kind':'object','handle':Client句柄(值['handle'])} if 值.get('kind')=='object' else 值#对象改句柄

def _断言求值选项(请求):#断言求值选项
    """拒绝不支持选项。"""
    if 请求.get('context') is not None:#上下文
        raise RuntimeError('Client Runtime does not support native execution contexts')#抛错
    if 请求.get('throwOnSideEffect') is True:#副作用
        raise RuntimeError('Client Runtime does not support throwOnSideEffect')#抛错
    if 请求.get('serializationOptions') is not None:#序列化
        raise RuntimeError('Client Runtime does not support serializationOptions')#抛错
    if 请求.get('disableBreaks') is True:#禁用断点
        raise RuntimeError('Client Runtime does not support disableBreaks')#抛错
    if 请求.get('allowUnsafeEvalBlockedByCSP') is True:#CSP
        raise RuntimeError('Client Runtime cannot bypass the page Content Security Policy')#不能绕过
    if 请求.get('timeoutMs') is not None and 请求.get('awaitPromise') is not True:#超时
        raise RuntimeError('Client Runtime supports timeout only when awaitPromise is enabled')#仅await时

def _断言调用选项(请求):#断言调用选项
    """拒绝不支持选项。"""
    if 请求.get('context') is not None:#上下文
        raise RuntimeError('Client Runtime does not support native execution contexts')#抛错
    if 请求.get('throwOnSideEffect') is True:#副作用
        raise RuntimeError('Client Runtime does not support throwOnSideEffect')#抛错
    if 请求.get('serializationOptions') is not None:#序列化
        raise RuntimeError('Client Runtime does not support serializationOptions')#抛错
    if 请求.get('userGesture') is True:#手势
        raise RuntimeError('Client Runtime does not support userGesture')#抛错
