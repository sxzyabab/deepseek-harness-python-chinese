"""每个 DevTools 会话上，跨 Host 与 Client realm 的 Debugger 与源路由。

对齐上游 `worker/cdp/domains/debugger/session.ts`。公开面仅中文名。
"""
from .......内核.智能体循环.辅助 import 解开,在线程跑#可等待则等待|后台跑
from .....共享.校验 import 精确键,可选布尔#校验
from ...协议 import 响应cdp请求,发送cdp失败#协议
from .cdp参数 import 解析调用帧求值,取请求脚本id#参数解析
from .投影器 import 调试器事件,脚本已解析事件#投影
from .脚本注册表 import 调试器脚本注册表#脚本注册表

__all__=['Debugger域会话']#仅中文公开名

class Debugger域会话:#Debugger域会话
    """拥有 Debugger 生命周期、共享脚本投影与 Host 原生回退。"""
    def __init__(自身,传输,realms,运行时):#构造
        """装配脚本表并订阅 realm。"""
        自身.传输=传输#传输
        自身.realms=realms#会话集
        自身.运行时=运行时#Runtime
        自身._脚本=调试器脚本注册表()#脚本注册表
        自身._源释放器={}#源释放器
        自身._调试释放器={}#调试释放器
        自身._调用帧realms={}#调用帧realm
        原生=None#原生后端
        for realm in realms.全部():#找支持的
            能力=_能力(realm.nativeDomains)#能力
            if 能力['state']=='supported':#支持
                原生=能力['backend']#后端
                break#找到
        if 原生 is None:#无原生
            raise Exception('Inspector has no native Host debugger transport')#抛错
        自身._原生=原生#保存后端
        自身._取消realm订阅=realms.订阅(自身._接收realm)#订阅
        自身._启用请求={}#启用请求
        自身._已启用=False#是否启用
        自身._已关闭=False#是否关闭

    def 处理(自身,请求):#处理请求
        """处理一条 Debugger 请求，包括 Client 只读源操作。"""
        if not 请求['method'].startswith('Debugger.'):#非Debugger
            return False#未拥有
        方法=请求['method']#方法
        if 方法=='Debugger.enable':#启用
            自身._响应(请求,lambda:自身._启用(请求['params']))#响应
            return True#已拥有
        if 方法=='Debugger.disable':#禁用
            精确键(请求['params'],[],'Debugger.disable parameters')#无参
            自身._响应(请求,自身._禁用)#响应
            return True#已拥有
        if 方法=='Debugger.getScriptSource':#取源
            自身._响应(请求,lambda:自身._取脚本来源(请求['params']))#响应
            return True#已拥有
        if 方法=='Debugger.searchInContent':#搜索
            自身._响应(请求,lambda:自身._内容搜索(请求['params']))#响应
            return True#已拥有
        if 方法=='Debugger.evaluateOnCallFrame':#帧求值
            自身._响应(请求,lambda:自身._帧上求值(请求['params']))#响应
            return True#已拥有
        if 方法=='Debugger.pause':#暂停
            精确键(请求['params'],[],'Debugger.pause parameters')#无参
            自身._响应(请求,自身._暂停)#响应
            return True#已拥有
        if 方法=='Debugger.resume':#恢复
            自身._响应(请求,lambda:自身._恢复(请求['params']))#响应
            return True#已拥有
        自身._转发原生(请求)#转发原生
        return True#已拥有

    def 关闭(自身):#关闭
        """释放源与调试器订阅。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身._取消realm订阅()#取消订阅
        自身._卸能力()#卸能力
        自身._调用帧realms.clear()#清帧
        自身._脚本.清空()#清脚本
        自身.运行时.释放投影组('backtrace')#释回溯组

    def _启用(自身,参数):#启用
        """Debugger.enable。"""
        精确键(参数,['maxScriptsCacheSize'],'Debugger.enable parameters')#键
        if 自身._已启用:#已启用
            return {}#空
        缓存=参数.get('maxScriptsCacheSize')#缓存大小
        if 缓存 is not None and (not isinstance(缓存,(int,float)) or isinstance(缓存,bool) or not (缓存==缓存) or 缓存<0):#非法
            raise Exception('Debugger.enable maxScriptsCacheSize must be a non-negative number')#抛错
        启用请求={} if 缓存 is None else {'maxScriptsCacheSize':缓存}#启用请求
        自身._启用请求=启用请求#保存
        自身._已启用=True#置位
        try:#启用各realm
            for 领域 in 自身.realms.全部():#附着
                自身._附着能力(领域)#附着能力
            结果们=[]#结果
            for 领域 in 自身.realms.全部():#逐个启用
                调试=_能力(领域.debugger)#能力
                结果们.append(解开(调试['backend'].启用(启用请求)) if 调试['state']=='supported' else {})#启用或空
            for 领域 in 自身.realms.全部():#发布目录
                自身._发布目录(领域)#发布
            return 合并结果(结果们)#合并结果
        except Exception:#失败回滚
            自身._已启用=False#清位
            自身._启用请求={}#清空请求
            自身._卸能力()#卸能力
            自身._脚本.清空()#清脚本
            for 领域 in 自身.realms.全部():#尽力禁用
                调试=_能力(领域.debugger)#能力
                if 调试['state']=='supported':#支持
                    try:#禁用
                        解开(调试['backend'].禁用())#禁用
                    except Exception:#忽略
                        pass#忽略
            raise#再抛

    def _禁用(自身):#禁用
        """Debugger.disable。"""
        自身._已启用=False#清位
        自身._启用请求={}#清空
        自身._卸能力()#卸能力
        自身._调用帧realms.clear()#清帧
        自身._脚本.清空()#清脚本
        自身.运行时.释放投影组('backtrace')#释回溯
        结果们=[]#结果
        for 领域 in 自身.realms.全部():#逐个禁用
            调试=_能力(领域.debugger)#能力
            结果们.append(解开(调试['backend'].禁用()) if 调试['state']=='supported' else {})#禁用或空
        return 合并结果(结果们)#合并

    def _取脚本来源(自身,参数):#取脚本来源
        """Debugger.getScriptSource。"""
        精确键(参数,['scriptId'],'Debugger.getScriptSource parameters')#键
        if not isinstance(参数.get('scriptId'),str):#类型
            raise Exception('Debugger.getScriptSource requires scriptId')#抛错
        路由=自身._脚本.解析(参数['scriptId'])#路由
        if 路由 is not None:#本地
            return {'scriptSource':解开(路由['source'].取脚本来源(路由['script']['scriptKey']))}#本地
        if 自身._脚本.曾不支持(参数['scriptId']) or 参数['scriptId'].startswith('client:'):#Client失效
            raise Exception('Client script is no longer available')#抛错
        return 解开(自身._原生.请求('Debugger.getScriptSource',参数))#原生

    def _内容搜索(自身,参数):#内容搜索
        """Debugger.searchInContent。"""
        精确键(参数,['scriptId','query','caseSensitive','isRegex'],'Debugger.searchInContent parameters')#键
        if not isinstance(参数.get('scriptId'),str) or not isinstance(参数.get('query'),str):#缺必填
            raise Exception('Debugger.searchInContent requires scriptId and query')#抛错
        if 参数.get('caseSensitive') is not None and not isinstance(参数['caseSensitive'],bool):#大小写类型
            raise Exception('Debugger.searchInContent caseSensitive must be a boolean')#抛错
        if 参数.get('isRegex') is not None and not isinstance(参数['isRegex'],bool):#正则类型
            raise Exception('Debugger.searchInContent isRegex must be a boolean')#抛错
        路由=自身._脚本.解析(参数['scriptId'])#路由
        if 路由 is None:#无本地
            if 自身._脚本.曾不支持(参数['scriptId']) or 参数['scriptId'].startswith('client:'):#Client失效
                raise Exception('Client script is no longer available')#抛错
            return 解开(自身._原生.请求('Debugger.searchInContent',参数))#原生
        源=解开(路由['source'].取脚本来源(路由['script']['scriptKey']))#取源
        return {'result':按行搜索(源,参数['query'],参数.get('caseSensitive') is True,参数.get('isRegex') is True)}#结果

    def _帧上求值(自身,参数):#帧上求值
        """Debugger.evaluateOnCallFrame。"""
        解析=解析调用帧求值(参数)#解析
        if 解析['callFrameId'].startswith('client:'):#Client不可用
            raise Exception('Client native debugging is unavailable')#抛错
        领域=自身._调用帧realms.get(解析['callFrameId']) or 自身._支持调试的()#领域
        对象组=解析.get('objectGroup') or 'backtrace'#对象组
        完成=解开(调试后端(领域).帧上求值({**解析,'objectGroup':对象组}))#求值
        return 自身.运行时.投影完成(领域,完成,对象组)#投影

    def _暂停(自身):#暂停
        """Debugger.pause。"""
        支持=[领域 for 领域 in 自身.realms.全部() if _能力(领域.debugger)['state']=='supported']#支持的
        if len(支持)==0:#全不支持
            raise Exception('Debugger.pause is unsupported by every active realm')#抛错
        结果们=[解开(调试后端(领域).暂停()) for 领域 in 支持]#逐个暂停
        return 合并结果(结果们)#合并

    def _恢复(自身,参数):#恢复
        """Debugger.resume。"""
        精确键(参数,['terminateOnResume'],'Debugger.resume parameters')#键
        请求=可选布尔(参数,'terminateOnResume')#可选
        支持=[领域 for 领域 in 自身.realms.全部() if _能力(领域.debugger)['state']=='supported']#支持的
        if len(支持)==0:#全不支持
            raise Exception('Debugger.resume is unsupported by every active realm')#抛错
        结果们=[解开(调试后端(领域).恢复(请求)) for 领域 in 支持]#逐个恢复
        return 合并结果(结果们)#合并

    def _转发原生(自身,请求):#转发原生
        """转发原生 Debugger 方法。"""
        try:#校验路由
            不支持=自身._不支持路由(请求['params'])#不支持原因
            if 不支持 is not None:#有
                raise Exception(不支持)#抛错
            参数=自身.运行时.原生参数(请求['params'])#本地化参数
        except Exception as 错误:#失败
            发送cdp失败(自身.传输,请求,错误)#失败响应
            return#返回
        响应cdp请求(自身.传输,请求,lambda:自身._原生.请求(请求['method'],参数))#原生请求

    def _不支持路由(自身,参数):#不支持路由
        """检查不支持原因。"""
        脚本id=取请求脚本id(参数)#脚本id
        if 脚本id is not None:#有脚本
            路由=自身._脚本.解析(脚本id)#路由
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
            if 路由 is None and 自身._脚本.曾不支持(脚本id):#已退役
                return 'Client script is no longer available'#原因
        if isinstance(参数.get('url'),str):#有URL
            路由=自身._脚本.按url(参数['url'])#按URL
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        if isinstance(参数.get('urlRegex'),str):#有正则
            路由=自身._脚本.按url模式(参数['urlRegex'])#按模式
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        if isinstance(参数.get('scriptHash'),str):#有哈希
            路由=自身._脚本.按哈希(参数['scriptHash'])#按哈希
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        if isinstance(参数.get('objectId'),str):#有对象
            路由=自身.运行时.对象路由(参数['objectId'])#对象路由
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        return None#可转发

    def _接收realm(自身,事件):#处理realm事件
        """打开或关闭。"""
        if 事件['type']=='opened':#打开
            if 自身._已启用:#已启用
                def 启():#启用体
                    """启用单个 realm。"""
                    try:#启用
                        自身._启用realm(事件['session'])#启用
                    except Exception as 错误:#失败
                        print(f'Inspector could not enable Debugger realm {事件["session"].descriptor.label}:',错误)#记录
                在线程跑(启)#投递
            return#返回
        会话=事件['session']#会话
        源释=自身._源释放器.pop(会话.descriptor.realmId,None)#释源
        if 源释 is not None:#有
            源释()#回调
        调释=自身._调试释放器.pop(会话.descriptor.realmId,None)#释调试
        if 调释 is not None:#有
            调释()#回调
        for 帧id,所有者 in list(自身._调用帧realms.items()):#扫帧
            if 所有者 is 会话:#同会话
                del 自身._调用帧realms[帧id]#删除
        自身._脚本.移除realm(会话)#移除脚本

    def _启用realm(自身,领域):#启用单个realm
        """附着并启用。"""
        自身._附着能力(领域)#附着
        调试=_能力(领域.debugger)#能力
        if 调试['state']=='supported':#支持
            解开(调试['backend'].启用(自身._启用请求))#启用
        自身._发布目录(领域)#发布目录

    def _附着能力(自身,领域):#附着能力
        """附着源与调试订阅。"""
        源=_能力(领域.sources)#源能力
        if 源['state']=='supported' and 领域.descriptor.realmId not in 自身._源释放器:#源未附着
            后端=源['backend']#源后端
            自身._源释放器[领域.descriptor.realmId]=后端.订阅(lambda 脚本:自身._发布脚本(领域,后端,脚本) if 自身._已启用 else None)#订阅脚本
        调试=_能力(领域.debugger)#调试能力
        if 调试['state']=='supported' and 领域.descriptor.realmId not in 自身._调试释放器:#调试未附着
            自身._调试释放器[领域.descriptor.realmId]=调试['backend'].订阅(lambda 事件:自身._发布调试事件(领域,事件) if 自身._已启用 else None)#订阅事件

    def _发布目录(自身,领域):#发布目录
        """列出并发布脚本。"""
        源=_能力(领域.sources)#源
        if not 自身._已启用 or 源['state']=='unsupported':#跳过
            return#返回
        脚本们=解开(源['backend'].列脚本())#列脚本
        for 脚本 in 脚本们:#发布
            自身._发布脚本(领域,源['backend'],脚本)#发布

    def _发布脚本(自身,realm,源,脚本):#发布脚本
        """注册并首次公告。"""
        注册=自身._脚本.注册({'realm':realm,'source':源,'script':脚本})#注册
        if 注册['fresh']:#首次
            自身.传输.发送(脚本已解析事件(realm,脚本))#公告

    def _发布调试事件(自身,realm,事件):#发布调试事件
        """暂停/恢复并投影。"""
        if 事件['type']=='paused':#暂停
            for 帧 in 事件['callFrames']:#记帧
                自身._调用帧realms[帧['callFrameId']]=realm#记帧
        elif 事件['type']=='resumed':#恢复
            for 帧id,所有者 in list(自身._调用帧realms.items()):#扫帧
                if 所有者 is realm:#同realm
                    del 自身._调用帧realms[帧id]#删除
            自身.运行时.释放投影组('backtrace')#释回溯
        自身.传输.发送(调试器事件(realm,事件,自身.运行时))#发送

    def _支持调试的(自身):#找支持调试的realm
        """找支持调试的 realm。"""
        for 候选 in 自身.realms.全部():#查找
            if _能力(候选.debugger)['state']=='supported':#支持
                return 候选#返回
        raise Exception('No active realm supports call-frame evaluation')#无

    def _卸能力(自身):#卸全部能力
        """卸全部能力。"""
        for 释放 in 自身._源释放器.values():#释源
            释放()#回调
        自身._源释放器.clear()#清源
        for 释放 in 自身._调试释放器.values():#释调试
            释放()#回调
        自身._调试释放器.clear()#清调试

    def _响应(自身,请求,操作):#响应请求
        """委托协议响应。"""
        响应cdp请求(自身.传输,请求,操作)#委托

def _能力(值):#能力面
    """统一 dict/对象能力。"""
    if isinstance(值,dict):#字典
        return 值#原样
    return {'state':值.state,'backend':getattr(值,'backend',None),'reason':getattr(值,'reason',None)}#对象面

def 调试后端(realm):#取调试后端
    """取调试后端。"""
    调试=_能力(realm.debugger)#能力
    if 调试['state']=='unsupported':#不支持
        raise Exception(调试['reason'])#抛错
    return 调试['backend']#返回

def 合并结果(结果们):#合并结果
    """合并多 realm 结果。"""
    合并={}#目标
    for 结果 in 结果们:#合并
        合并.update(结果)#合并
    return 合并#返回

def 按行搜索(源,查询,区分大小写,是正则):#按行搜索
    """按行搜索源文本。"""
    import re#正则
    表达式=re.compile(查询,0 if 区分大小写 else re.I) if 是正则 else None#正则
    期望=查询 if 区分大小写 else 查询.lower()#期望子串
    结果=[]#结果
    for 行号,行内容 in enumerate(源.split('\n')):#扫行
        命中=表达式.search(行内容) is not None if 表达式 is not None else (行内容 if 区分大小写 else 行内容.lower()).find(期望)>=0#匹配
        if 命中:#收录
            结果.append({'lineNumber':行号,'lineContent':行内容})#收录
    return 结果#返回
