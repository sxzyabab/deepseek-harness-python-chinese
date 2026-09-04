"""每个 DevTools 会话上，跨统一 Host 与 Client realm 的 Runtime 路由。

对齐上游 `worker/cdp/domains/runtime/session.ts`。公开面仅中文名。
"""
from .......内核.智能体循环.辅助 import 解开,在线程跑#可等待则等待|后台跑
from ...协议 import cdp错误,响应cdp请求#协议
from .cdp参数 import (#参数解析
    解析求值,解析取属性,解析调函数,解析等Promise,
    解析释放对象,解析释放对象组,解析全局词法作用域名,
)
from .对象表 import Runtime对象表#对象表

__all__=['Runtime域会话']#仅中文公开名

class Runtime域会话:#Runtime域会话
    """叠在公共每连接 realm 会话之上的 Runtime 路由器。"""
    def __init__(自身,传输,realms):#构造
        """装配对象表并订阅 realm。"""
        自身.传输=传输#传输
        自身.realms=realms#会话集
        自身._对象=Runtime对象表(realms.connectionId)#对象表
        自身._已公告上下文=set()#已公告上下文
        自身._控制台释放器={}#Console释放器
        自身._取消realm订阅=realms.订阅(自身._接收realm)#订阅
        自身._已启用=False#是否启用
        自身._已关闭=False#是否关闭

    def 处理(自身,请求):#处理请求
        """处理需要跨 realm Runtime 协调的方法。"""
        方法=请求['method']#方法
        if 方法=='Runtime.enable':#启用
            自身._响应(请求,自身._启用)#响应
            return True#已拥有
        if 方法=='Runtime.disable':#禁用
            自身._响应(请求,自身._禁用)#响应
            return True#已拥有
        if 方法=='Runtime.evaluate':#求值
            自身._响应(请求,lambda:自身._求值(请求['params']))#响应
            return True#已拥有
        if 方法=='Runtime.getProperties':#取属性
            return 自身._取属性(请求)#委托
        if 方法=='Runtime.callFunctionOn':#调函数
            return 自身._调函数(请求)#委托
        if 方法=='Runtime.awaitPromise':#等Promise
            return 自身._等Promise(请求)#委托
        if 方法=='Runtime.releaseObject':#释放对象
            return 自身._释放对象(请求)#委托
        if 方法=='Runtime.releaseObjectGroup':#释放组
            自身._响应(请求,lambda:自身._释放对象组(请求['params']))#响应
            return True#已拥有
        if 方法=='Runtime.globalLexicalScopeNames':#词法名
            自身._响应(请求,lambda:自身._全局词法作用域名(请求['params']))#响应
            return True#已拥有
        if 方法=='Runtime.discardConsoleEntries':#丢弃Console
            自身._响应(请求,自身._丢弃控制台条目)#响应
            return True#已拥有
        if 方法.startswith('Runtime.'):#Runtime族
            原因=自身._不支持原生路由(请求['params'])#不支持原因
            if 原因 is not None:#有原因
                自身._发错误(请求,原因)#错误
                return True#已拥有
        return False#未拥有

    def 关闭(自身):#关闭
        """释放本连接的对象路由与 realm 订阅。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身._取消realm订阅()#取消订阅
        for 释放 in 自身._控制台释放器.values():#释Console
            释放()#回调
        自身._控制台释放器.clear()#清Console
        自身._对象.清空()#清对象
        自身._已公告上下文.clear()#清公告

    def 设对象观察者(自身,观察者):#设对象观察者
        """安装与 DOM 适配器共享的语义对象识别。"""
        自身._对象.设观察者(观察者)#委托

    def 对象路由(自身,对象id):#对象路由
        """为其他域适配器解析一个连接本地 CDP 对象 id。"""
        return 自身._对象.解析(对象id)#解析

    def 投影完成(自身,领域,完成,组):#投影完成
        """将其他域产出的完成结果经本连接的对象表投影。"""
        return 自身._对象.完成(领域,完成,组)#委托

    def 投影远程对象(自身,领域,值,组):#投影远程对象
        """投影其他域产出的一个 Runtime 值。"""
        return 自身._对象.远程(领域,值,组)#委托

    def 释放投影组(自身,组):#释放投影组
        """忘记为其他域对象组保留的连接本地 id。"""
        自身._对象.释放组(组)#委托

    def 原生参数(自身,参数):#原生参数改写
        """在仅 Host 的请求中，将公共对象 id 替换为原生后端句柄。"""
        def 访问(值,键):#递归访问
            """递归改写。"""
            if (键=='objectId' or (isinstance(键,str) and 键.endswith('ObjectId'))) and isinstance(值,str):#对象id字段
                路由=自身._对象.解析(值)#解析路由
                if 路由 is None:#未知则保留
                    return 值#保留
                if getattr(路由['realm'].nativeDomains,'state',None)=='unsupported' or (isinstance(路由['realm'].nativeDomains,dict) and 路由['realm'].nativeDomains.get('state')=='unsupported'):#不支持
                    原因=路由['realm'].nativeDomains.reason if hasattr(路由['realm'].nativeDomains,'reason') else 路由['realm'].nativeDomains['reason']#原因
                    raise Exception(原因)#抛错
                return 路由['handle']#后端句柄
            if isinstance(值,list):#数组
                return [访问(项,None) for 项 in 值]#映射
            if not isinstance(值,dict) or 值 is None:#标量
                return 值#原样
            return {名:访问(项,名) for 名,项 in 值.items()}#对象
        return 访问(参数,None)#改写结果

    def 解析对象(自身,源,表达式,对象组):#解析对象表达式
        """将一个 realm 注册表表达式解析为连接本地对象 id。"""
        领域=自身.realms.按源(源)#取realm
        if 领域 is None:#已断
            raise Exception('Cordis realm is no longer connected')#抛错
        运行时=运行时后端(领域)#后端
        完成=解开(运行时.求值({'expression':表达式,'generatePreview':True,**({} if 对象组 is None else {'objectGroup':对象组})}))#求值
        if 完成.get('exceptionDetails') is not None:#失败
            raise Exception('Cordis object lookup failed')#抛错
        return 自身._对象.完成(领域,完成,对象组)['result']#结果

    def _启用(自身):#启用
        """启用各 realm Runtime。"""
        自身._已启用=True#置位
        try:#启用各realm
            for 领域 in 自身.realms.全部():#扫
                解开(运行时后端(领域).启用())#启用
            for 领域 in 自身.realms.全部():#扫realm
                自身._附着控制台(领域)#附着Console
                自身._公告(领域)#公告上下文
            return {}#空结果
        except Exception:#回滚
            自身._已启用=False#清位
            for 释放 in 自身._控制台释放器.values():#释Console
                释放()#回调
            自身._控制台释放器.clear()#清Console
            自身._已公告上下文.clear()#清公告
            for 领域 in 自身.realms.全部():#尽力禁用
                try:#禁用
                    解开(运行时后端(领域).禁用())#禁用
                except Exception:#忽略
                    pass#忽略
            raise#再抛

    def _禁用(自身):#禁用
        """禁用 Runtime。"""
        for 释放 in 自身._控制台释放器.values():#释Console
            释放()#回调
        自身._控制台释放器.clear()#清Console
        try:#禁用后端
            for 领域 in 自身.realms.全部():#逐个
                解开(运行时后端(领域).禁用())#禁用
        finally:#清理
            自身._已启用=False#清位
            自身._对象.清空()#清对象
            自身._已公告上下文.clear()#清公告
        return {}#空结果

    def _求值(自身,参数):#求值
        """Runtime.evaluate。"""
        解析=解析求值(参数)#解析
        领域=自身._按选择器取realm(解析,'contextId')#选realm
        完成=解开(运行时后端(领域).求值({**解析['request'],**自身._后端上下文(领域,解析,'contextId')}))#求值
        return 自身._对象.完成(领域,完成,解析['request'].get('objectGroup'))#投影

    def _取属性(自身,请求):#取属性
        """Runtime.getProperties。"""
        对象id=请求['params'].get('objectId')#对象id
        if not isinstance(对象id,str):#类型
            return False#未拥有
        路由=自身._对象.解析(对象id)#路由
        if 路由 is None:#未知
            return False#未拥有
        def 操作():#响应体
            """取属性并投影。"""
            解析=解析取属性(请求['params'])#解析
            属性=解开(运行时后端(路由['realm']).取属性({**解析['request'],'handle':路由['handle']}))#取属性
            return 自身._对象.属性们(路由['realm'],属性,路由['group'])#投影
        自身._响应(请求,操作)#响应
        return True#已拥有

    def _调函数(自身,请求):#调函数
        """Runtime.callFunctionOn。"""
        对象id=请求['params'].get('objectId') if isinstance(请求['params'].get('objectId'),str) else None#对象id
        接收者=None if 对象id is None else 自身._对象.解析(对象id)#接收者
        选中=自身._可选选择器取realm(请求['params'],'executionContextId')#选中realm
        if 接收者 is None and 选中 is None and 对象id is not None:#未知对象
            return False#未拥有
        领域=(接收者['realm'] if 接收者 is not None else None) or 选中 or 自身.realms.host()#目标realm
        if 接收者 is not None and 选中 is not None and 接收者['realm'] is not 选中:#跨realm
            自身._发错误(请求,'Runtime.callFunctionOn receiver and execution context belong to different realms')#错误
            return True#已拥有
        def 操作():#响应体
            """调函数并投影。"""
            解析=解析调函数(请求['params'])#解析
            组=解析['request'].get('objectGroup') or (接收者['group'] if 接收者 is not None else None)#组
            调用={**解析['request'],**自身._后端上下文(领域,解析,'executionContextId'),'arguments':[自身._路由参数(领域,项) for 项 in 解析['arguments']]}#调用
            if 接收者 is not None:#有接收者
                调用['receiver']=接收者['handle']#接收者
            完成=解开(运行时后端(领域).调函数(调用))#调函数
            return 自身._对象.完成(领域,完成,组)#投影
        自身._响应(请求,操作)#响应
        return True#已拥有

    def _等Promise(自身,请求):#等Promise
        """Runtime.awaitPromise。"""
        对象id=请求['params'].get('promiseObjectId')#Promise id
        if not isinstance(对象id,str):#类型
            return False#未拥有
        路由=自身._对象.解析(对象id)#路由
        if 路由 is None:#未知
            return False#未拥有
        def 操作():#响应体
            """等待并投影。"""
            解析=解析等Promise(请求['params'])#解析
            完成=解开(运行时后端(路由['realm']).等Promise({**解析['request'],'promise':路由['handle']}))#等待
            return 自身._对象.完成(路由['realm'],完成,路由['group'])#投影
        自身._响应(请求,操作)#响应
        return True#已拥有

    def _释放对象(自身,请求):#释放对象
        """Runtime.releaseObject。"""
        对象id=请求['params'].get('objectId')#对象id
        if not isinstance(对象id,str):#类型
            return False#未拥有
        路由=自身._对象.解析(对象id)#路由
        if 路由 is None:#未知
            return False#未拥有
        def 操作():#响应体
            """后端与表释放。"""
            解析释放对象(请求['params'])#校验
            解开(运行时后端(路由['realm']).释放对象(路由['handle']))#后端释放
            自身._对象.释放(对象id)#表释放
            return {}#空
        自身._响应(请求,操作)#响应
        return True#已拥有

    def _释放对象组(自身,参数):#释放对象组
        """Runtime.releaseObjectGroup。"""
        组=解析释放对象组(参数)#组名
        领域们=自身._对象.组内realms(组)#相关realm
        try:#后端释放
            for 领域 in 领域们:#逐个
                解开(运行时后端(领域).释放对象组(组))#释放
        finally:#表清理
            自身._对象.释放组(组)#释放组
        return {}#空

    def _全局词法作用域名(自身,参数):#词法作用域名
        """Runtime.globalLexicalScopeNames。"""
        解析=解析全局词法作用域名(参数)#解析
        领域=自身._按选择器取realm(解析,'executionContextId')#选realm
        上下文=自身._后端上下文(领域,解析,'executionContextId').get('context')#上下文
        return {'names':解开(运行时后端(领域).全局词法名(上下文))}#名称

    def _丢弃控制台条目(自身):#丢弃Console条目
        """Runtime.discardConsoleEntries。"""
        for 领域 in 自身.realms.全部():#逐个
            控制台=领域.console#Console能力
            状态=控制台['state'] if isinstance(控制台,dict) else 控制台.state#状态
            if 状态=='supported':#支持
                后端=控制台['backend'] if isinstance(控制台,dict) else 控制台.backend#后端
                解开(后端.清空())#清Console
            解开(运行时后端(领域).释放对象组('console'))#释console组
        自身._对象.释放组('console')#表释放
        return {}#空

    def _按选择器取realm(自身,参数,数字键):#按选择器取realm
        """缺省 Host。"""
        return 自身._可选选择器取realm(参数,数字键) or 自身.realms.host()#缺省Host

    def _可选选择器取realm(自身,参数,数字键):#可选选择器
        """可选上下文选择。"""
        数字=参数.get(数字键)#数字值
        if isinstance(数字,int) and not isinstance(数字,bool):#有效数字
            领域=自身.realms.按上下文id(数字)#按id
            if 领域 is not None:#命中
                return 领域#返回
            if 数字<0:#Client失效
                raise Exception('Client execution context is no longer available')#抛错
            return 自身.realms.host()#回退Host
        唯一=参数.get('uniqueContextId')#唯一id
        if isinstance(唯一,str):#有唯一
            领域=自身.realms.按唯一上下文id(唯一)#查找
            if 领域 is not None:#命中
                return 领域#返回
            if 唯一.startswith('dsh-client:'):#Client失效
                raise Exception('Client execution context is no longer available')#抛错
            return 自身.realms.host()#回退Host
        return None#无选择

    def _后端上下文(自身,领域,参数,数字键):#后端上下文
        """原生上下文包装。"""
        if 领域.context.kind!='native':#非原生
            return {}#空
        数字=参数.get(数字键)#数字
        if isinstance(数字,int) and not isinstance(数字,bool):#数字上下文
            return {'context':{'kind':'numeric','id':数字}}#数字上下文
        if 参数.get('uniqueContextId') is None:#无唯一
            return {}#空
        return {'context':{'kind':'unique','id':参数['uniqueContextId']}}#唯一上下文

    def _路由参数(自身,领域,参数):#路由调用参数
        """对象参数须同 realm。"""
        if 参数['kind']!='object':#非对象
            return 参数#原样
        路由=自身._对象.解析(参数['objectId'])#路由
        if 路由 is None or 路由['realm'] is not 领域:#跨realm或未知
            raise Exception('Runtime.callFunctionOn cannot pass an object between realms')#抛错
        return {'kind':'object','handle':路由['handle']}#句柄

    def _不支持原生路由(自身,参数):#不支持原生路由
        """检查不支持原因。"""
        for 键 in ('contextId','executionContextId'):#上下文键
            上下文id=参数.get(键)#取值
            if not isinstance(上下文id,int) or isinstance(上下文id,bool):#非数字
                continue#跳过
            领域=自身.realms.按上下文id(上下文id)#取realm
            原生=_能力(领域.nativeDomains) if 领域 is not None else None#原生
            if 原生 is not None and 原生['state']=='unsupported':#不支持
                return 原生['reason']#原因
            if 上下文id<0 and 领域 is None:#失效
                return 'Client execution context is no longer available'#原因
        if isinstance(参数.get('uniqueContextId'),str):#唯一上下文
            领域=自身.realms.按唯一上下文id(参数['uniqueContextId'])#查找
            原生=_能力(领域.nativeDomains) if 领域 is not None else None#原生
            if 原生 is not None and 原生['state']=='unsupported':#不支持
                return 原生['reason']#原因
            if 参数['uniqueContextId'].startswith('dsh-client:') and 领域 is None:#Client失效
                return 'Client execution context is no longer available'#原因
        for 键,值 in 参数.items():#扫字段
            if not 键.endswith('ObjectId') and 键!='objectId':#非对象id
                continue#跳过
            if not isinstance(值,str):#非字符串
                continue#跳过
            路由=自身._对象.解析(值)#路由
            if 路由 is None:#无
                continue#跳过
            原生=_能力(路由['realm'].nativeDomains)#原生
            if 原生['state']=='unsupported':#不支持
                return 原生['reason']#原因
        return None#可转发

    def _接收realm(自身,事件):#处理realm事件
        """打开或关闭。"""
        if 事件['type']=='opened':#打开
            if 自身._已启用:#已启用
                def 启用():#启用体
                    """启用后端。"""
                    try:#成功
                        解开(运行时后端(事件['session']).启用())#启用
                        自身._附着控制台(事件['session'])#附着Console
                        自身._公告(事件['session'])#公告
                    except Exception:#失败
                        事件['session'].关闭()#关会话
                在线程跑(启用)#投递
            return#返回
        会话=事件['session']#会话
        释放=自身._控制台释放器.pop(会话.descriptor.realmId,None)#释Console
        if 释放 is not None:#有
            释放()#回调
        自身._对象.释放realm(会话)#释对象
        自身._销毁(会话)#销毁上下文

    def _附着控制台(自身,领域):#附着Console
        """订阅 Console。"""
        控制台=_能力(领域.console)#能力
        if 控制台['state']=='unsupported' or 领域.descriptor.realmId in 自身._控制台释放器:#跳过
            return#返回
        def 收(事件):#事件回调
            """转发控制台事件。"""
            if not 自身._已启用:#未启用
                return#返回
            自身.传输.发送(自身._对象.控制台事件(领域,事件))#发送
        自身._控制台释放器[领域.descriptor.realmId]=控制台['backend'].订阅(收)#订阅

    def _公告(自身,领域):#公告上下文
        """公告合成上下文。"""
        if not 自身._已启用 or 领域.context.kind!='synthetic' or 领域.context.id in 自身._已公告上下文:#跳过
            return#返回
        自身._已公告上下文.add(领域.context.id)#记公告
        自身.传输.发送({#发送创建
            'method':'Runtime.executionContextCreated',#方法
            'params':{'context':{#上下文
                'id':领域.context.id,#id
                'uniqueId':领域.context.uniqueId,#唯一id
                'origin':领域.context.origin,#origin
                'name':f'Client — {领域.descriptor.label}',#名称
                'auxData':{'isDefault':False,'type':'dsh-client','sourceId':领域.descriptor.sourceId},#辅助
            }},#params结束
        })#send结束

    def _销毁(自身,领域):#销毁上下文
        """销毁合成上下文。"""
        if 领域.context.kind!='synthetic' or 领域.context.id not in 自身._已公告上下文:#跳过
            return#返回
        自身._已公告上下文.discard(领域.context.id)#删公告
        自身.传输.发送({#发送销毁
            'method':'Runtime.executionContextDestroyed',#方法
            'params':{'executionContextId':领域.context.id,'executionContextUniqueId':领域.context.uniqueId},#参数
        })#send结束

    def _响应(自身,请求,操作):#响应请求
        """委托协议响应。"""
        响应cdp请求(自身.传输,请求,操作)#委托

    def _发错误(自身,请求,信息):#发送错误
        """发送错误响应。"""
        自身.传输.发送(cdp错误(请求['id'],-32000,信息))#错误响应

def _能力(值):#能力面
    """统一 dict/对象能力。"""
    if isinstance(值,dict):#字典
        return 值#原样
    return {'state':值.state,'backend':getattr(值,'backend',None),'reason':getattr(值,'reason',None)}#对象面

def 运行时后端(领域):#取Runtime后端
    """取 Runtime 后端。"""
    运行时=_能力(领域.runtime)#能力
    if 运行时['state']=='unsupported':#不支持
        raise Exception(运行时['reason'])#抛错
    return 运行时['backend']#返回
