"""模型安全的会话检索调用与错误翻译边界。对齐上游 `tool-session-query/src/service-boundary.ts`。"""
from ...模型后端.llm import 装备错误,错误链#Harness错误与错误链
from ..会话查询 import 会话查询错误#检索错误

不可打印服务错误='[unprintable session query failure]'#无法打印的失败占位

安全会话查询失败={
    'SESSION_QUERY_ABORTED':{'code':'SESSION_QUERY_ABORTED','message':'session query was cancelled'},
    'SESSION_QUERY_CORRUPT_SESSION':{'code':'SESSION_QUERY_CORRUPT_SESSION','message':'session event history is corrupt'},
    'SESSION_QUERY_EVENT_NOT_FOUND':{'code':'SESSION_QUERY_EVENT_NOT_FOUND','message':'session event was not found'},
    'SESSION_QUERY_INDEX_FAILED':{'code':'SESSION_QUERY_INDEX_FAILED','message':'session search index is unavailable'},
    'SESSION_QUERY_INVALID_CONFIG':{'code':'SESSION_QUERY_TOOL_FAILED','message':'session query operation failed'},
    'SESSION_QUERY_INVALID_CURSOR':{'code':'SESSION_QUERY_INVALID_CURSOR','message':'session search continuation is invalid'},
    'SESSION_QUERY_INVALID_FILTER':{'code':'SESSION_QUERY_INVALID_FILTER','message':'session query filters were rejected'},
    'SESSION_QUERY_INVALID_LIMIT':{'code':'SESSION_QUERY_INVALID_LIMIT','message':'session query result limit was rejected'},
    'SESSION_QUERY_INVALID_QUERY':{'code':'SESSION_QUERY_INVALID_QUERY','message':'session query was rejected'},
    'SESSION_QUERY_INVALID_LINEAGE':{'code':'SESSION_QUERY_INVALID_LINEAGE','message':'session lineage is invalid'},
    'SESSION_QUERY_INVALID_SURFACE':{'code':'SESSION_QUERY_INVALID_SURFACE','message':'session event history is invalid'},
    'SESSION_QUERY_INVALID_WINDOW':{'code':'SESSION_QUERY_INVALID_WINDOW','message':'session event window is invalid'},
    'SESSION_QUERY_PERSISTENCE_FAILED':{'code':'SESSION_QUERY_PERSISTENCE_FAILED','message':'session history storage is unavailable'},
    'SESSION_QUERY_SEARCH_DISABLED':{'code':'SESSION_QUERY_SEARCH_DISABLED','message':'session search is disabled in this deployment'},
    'SESSION_QUERY_SESSION_NOT_FOUND':{'code':'SESSION_QUERY_SESSION_NOT_FOUND','message':'session was not found'},
    'SESSION_QUERY_STALE_CURSOR':{'code':'SESSION_QUERY_STALE_CURSOR','message':'session history changed while paging; retry the complete search call'},
    'SESSION_QUERY_SOURCE_CONFLICT':{'code':'SESSION_QUERY_TOOL_FAILED','message':'session query operation failed'},
}#安全失败表

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否thenable(值):#判定可等待对象
    """判定值是否可等待。"""
    if 值 is None:#空不是
        return False#不是
    return callable(getattr(值,'wait',None)) or callable(getattr(值,'等待',None))#Future或thenable

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        if callable(getattr(值,'wait',None)):#Future风格
            return 值.wait()#等待
        return 值.等待()#thenable
    return 值#同步值

def 信号已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return getattr(信号,'aborted',False) is True or getattr(信号,'已中止',False) is True#中英旗标

def 未授权目标():#工作区外目标
    """工作区外目标的稳定未授权错误。"""
    return 装备错误('session target is outside the caller workspace','SESSION_QUERY_TOOL_UNAUTHORIZED')#未授权

def 调用(上下文,信号,操作名,执行):#内含一次服务调用
    """内含一次服务调用并消毒错误。"""
    if 信号已中止(信号):#已取消
        raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消
    try:#执行服务
        值=解开(执行())#等待结果
        if 信号已中止(信号):#返回前再检取消
            raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消
        return 值#原样返回
    except Exception as 错误:#服务失败
        if 信号已中止(信号):#取消优先
            raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消
        raise 消毒错误(上下文,操作名,错误)#抛出模型安全错误

def 消毒错误(上下文,操作名,错误):#把失败收成模型安全错误
    """把任意失败收成模型安全 Harness 错误。"""
    通用=通用失败()#通用失败
    try:#记日志并翻译
        上下文.logger.warn(f'tool-session-query: {操作名} failed: {完整错误(错误)}')#宿主日志
        if isinstance(错误,会话查询错误):#已知检索错误
            码=取字段(错误,'code')#错误码
            失败=安全会话查询失败.get(码) if isinstance(码,str) else None#查表
            if 失败 is not None and 失败['code']!='SESSION_QUERY_TOOL_FAILED':#可暴露
                return 会话查询错误(失败['message'],失败['code'])#安全重建
        if isinstance(错误,装备错误) and 取字段(错误,'code')=='SESSION_QUERY_TOOL_UNAUTHORIZED':#已是未授权
            return 未授权目标()#稳定未授权
    except Exception:#日志或翻译自己又抛
        return 通用#退回通用
    return 通用#其余一律通用

def 通用失败():return 装备错误('session query operation failed','SESSION_QUERY_TOOL_FAILED')#通用工具失败

def 完整错误(错误):#完整诊断
    """渲染错误及 cause 链。"""
    try:#尝试渲染
        return 渲染完整错误(错误)#含cause链
    except Exception:#渲染失败
        return 不可打印服务错误#占位

def 渲染完整错误(错误):#渲染错误及cause链
    """渲染 Error 及 cause 链。"""
    if not isinstance(错误,BaseException):#非异常
        return str(错误)#字符串化
    诊断=[错误链(错误)]#栈或消息
    return '\nCaused by: '.join(诊断)#拼链

服务边界={'unauthorizedTarget':未授权目标,'call':调用,'sanitizeError':消毒错误}#对外出口
