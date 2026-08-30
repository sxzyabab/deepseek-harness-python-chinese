"""通过 Cordis 服务与已注册提供方做在线 Typert Remote 分发。

对齐上游 `api/gateway/src/index.ts`。公开面仅中文名。传输、请求关联与响应信封属于 Connection。
"""
import inspect,re#参数名与标识符
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from ...typert.协议 import 远程方法们,查找策略失败#Remote 标记与查找失败

__all__=[#仅中文公开名
    '网关错误','Typert网关服务','TypertGatewayService','TypertGatewayError',
]#公开面结束

标识符模式=re.compile(r'^[$A-Z_a-z][$\w]*$')#SRC 参数名
永未中止=type('中止信号',(),{'aborted':False})()#永未中止的取消信号占位

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 是否对象(值):#判断是否为对象或可调用
    """非 None 对象或函数。"""
    return (isinstance(值,object) and 值 is not None and not isinstance(值,(str,bytes,bytearray,int,float,bool))) or callable(值)#对象或函数

def 是否普通对象(值):#判断是否为普通映射
    """数组不是普通对象；要求 dict。"""
    return isinstance(值,dict)#普通 dict

def 拼端点(命名空间,方法):#拼规范端点
    """返回 namespace/method。"""
    return 命名空间+'/'+方法#端点

def 取原始(接收方):#去掉 Cordis 代理得到原始对象
    """有原始符号则用之。"""
    try:#可能不可读
        原始=getattr(接收方,符号.原始,None)#读原始
    except Exception:#失败
        原始=None#无
    if 原始 is None and isinstance(接收方,dict):#映射形
        原始=接收方.get(符号.原始)#尝试键
    return 原始 if 是否对象(原始) else 接收方#有则用，否则自身

class 网关错误(Exception):#网关分发失败
    """在被调业务方法之外产生的分发失败。"""
    def __init__(自身,码,端点,消息,选项=None):#构造
        """消息中不嵌入边界值。"""
        if 选项 is None:#缺省
            选项={}#空
        原因=选项.get('cause')#可选原因
        全文='typert gateway: '+端点+': '+消息#带端点前缀
        if 原因 is not None:#有原因
            super().__init__(全文)#构造
            自身.__cause__=原因 if isinstance(原因,BaseException) else None#挂原因
        else:#无原因
            super().__init__(全文)#构造
        自身.name='TypertGatewayError'#固定错误名
        自身.code=码#失败类别
        自身.endpoint=端点#端点
        自身.field=选项.get('field')#可选线字段

TypertGatewayError=网关错误#上游名

class 远程调用已取消(Exception):#业务调用输掉了载体取消竞态
    """Remote 调用已被取消。"""
    def __init__(自身,端点,原因):#构造
        """记下端点与原因。"""
        super().__init__('Remote invocation "'+端点+'" was aborted')#消息
        自身.name='RemoteInvocationCancelled'#错误名
        自身.__cause__=原因 if isinstance(原因,BaseException) else None#原因

class Typert网关服务(服务):#网关服务实现
    """用严格生成定义或保守 SRC 标记，对照当前 Cordis 服务与 Typert 提供方做解析。"""
    inject=['typert']#依赖 typert
    注入=['typert']#中文别名

    def __init__(自身,上下文):#构造并挂载网关
        """向活动的 Typert 注册表登记网关。"""
        super().__init__(上下文,'typertGateway')#以 typertGateway 名注册
        自身.源声明=None#SRC 端点声明缓存
        def 服务变更(*_位置参数,**_关键字参数):#服务变更时丢弃 SRC 缓存
            """下次认领时重新收集。"""
            自身.源声明=None#清空
        上下文.on('internal/service',服务变更)#监听
        def 挂连接(连接上下文):#等 connection 可用后拦截 RPC
            """拦截 /api 下的远程调用。"""
            连接=连接上下文.connection#连接服务
            连接.rpc.intercept(#拦截
                '/api',#路径前缀
                lambda 端点:自身.认领端点(端点),#是否认领
                lambda 端点,载荷,信号:自身.分发RPC(端点,载荷,信号),#分发
                {'authority':'trusted-host'},#仅受信宿主
            )#拦截结束
        上下文.inject(['connection'],挂连接)#等 connection

    def 认领端点(自身,端点):#判断本网关是否认领该端点
        """两端非空；严格定义/曾见或 SRC 声明命中则认领。"""
        段=端点.split('/')#拆
        if len(段)!=2 or 段[0]=='' or 段[1]=='':#非法
            return False#不认领
        if 自身.ctx.typert.local.get(端点) is not None or 自身.ctx.typert.local.hasSeen(端点):#严格或曾见
            return True#认领
        if 自身.源声明 is None:#惰性收集
            自身.源声明=自身.收集源声明()#收集
        return 端点 in 自身.源声明#SRC 命中

    def 收集源声明(自身):#从活动服务收集 SRC 端点声明
        """遍历反射属性定义上的 typertRemote 绑定。"""
        声明=set()#端点集合
        属性表=getattr(自身.ctx.reflect,'属性表',None) or getattr(自身.ctx.reflect,'props',{})#属性定义
        项们=属性表.items() if hasattr(属性表,'items') else []#迭代
        for 服务键,定义 in 项们:#遍历
            if (定义.get('type') if isinstance(定义,dict) else getattr(定义,'type',None))!='service':#只看服务
                continue#跳过
            接收方=自身.ctx.get(服务键)#活动接收方
            if not 是否对象(接收方):#非对象
                continue#跳过
            原始=取原始(接收方)#原始对象
            绑定=getattr(原始,'typertRemote',None)#绑定
            if not isinstance(绑定,dict) or not isinstance(绑定.get('namespace'),str):#无效
                continue#跳过
            命名空间=绑定['namespace']#命名空间
            for 候选 in 远程方法们(原始):#枚举 Remote 方法
                方法=候选.get('exportName') or 候选['method']#导出名或方法名
                声明.add(拼端点(命名空间,方法))#加入
        return 声明#集合

    def invoke(自身,请求):#分发一次远程调用
        """通过严格生成反射或 SRC 标记调用一个在线 Remote 方法。"""
        端点=拼端点(请求['namespace'],请求['method'])#拼端点
        描述符=自身.解析描述符(请求['namespace'],请求['method'],端点)#解析
        断言精确参数(请求['args'],描述符,端点)#校验 args
        接收上下文=自身.解析接收上下文(描述符,请求['args'],端点)#接收方上下文
        接收方=接收上下文.get(描述符['service'])#活动服务
        if not 是否对象(接收方):#不可用
            raise 网关错误('service-unavailable',端点,'active Service '+repr(描述符['service'])+' is unavailable')#抛出
        校验绑定(接收方,描述符['service'],描述符['namespace'],端点)#校验绑定
        参数值=[]#业务参数
        for 参数 in 描述符['parameters']:#逐个
            参数值.append(自身.解析参数(参数,请求['args'],端点))#解析
        if 描述符.get('cancellation') is not None:#感知取消
            参数值.append(请求.get('signal') if 请求.get('signal') is not None else 永未中止)#补信号
        实现=描述符.get('implementation') or 描述符['method']#实际方法名
        方法=getattr(接收方,实现,None)#取实现
        if not callable(方法):#不可调用
            raise 网关错误('method-unavailable',端点,'active Service '+repr(描述符['service'])+' has no callable method '+repr(实现))#抛出
        try:#调用业务
            结果=解开(方法(*参数值))#应用参数
        except BaseException as 错误:#业务抛错
            信号=请求.get('signal')#取消信号
            if 信号 is not None and getattr(信号,'aborted',False):#载体已取消
                raise 远程调用已取消(端点,错误)#改标取消
            raise#原样抛出
        if 结果 is None and 描述符['result'].get('mode')!='strict':#弱描述符的 void
            return 结果#直接返回
        return 解码(描述符['result'],结果,'result-invalid',端点,'result')#边界校验

    def 分发RPC(自身,端点,载荷,信号):#RPC 拦截入口
        """转到 invokeRpc。"""
        return 自身.调用RPC(端点,载荷,信号)#委托

    def 调用RPC(自身,端点,载荷,信号):#把 RPC 信封转成 invoke 并包回结果
        """成功带 value；失败折成信封。"""
        try:#解析后调用
            段=端点.split('/')#拆端点
            if len(段)!=2 or 段[0]=='' or 段[1]=='':#非法
                raise Exception('invalid Remote endpoint '+repr(端点))#端点无效
            命名空间,方法=段[0],段[1]#拆出
            if not 是否对象(载荷) or not 是否普通对象(载荷) or list(载荷.keys())!=['args'] or not 是否普通对象(载荷['args']):#载荷形状
                raise Exception('Remote payload must contain exactly one plain-object args field')#必须恰好 args
            值=自身.invoke({'namespace':命名空间,'method':方法,'args':载荷['args'],'signal':信号})#分发
            return {'ok':True,'value':值}#成功信封
        except BaseException as 错误:#失败
            return RPC失败(错误)#折成失败

    def 解析描述符(自身,命名空间,方法,端点):#解析端点对应的调用描述符
        """有严格定义用之；曾见但已撤回禁止 SRC；否则 SRC。"""
        严格=自身.ctx.typert.local.get(端点)#严格定义
        if 严格 is not None:#有
            return 严格#用之
        if 自身.ctx.typert.local.hasSeen(端点):#曾见但撤回
            raise 网关错误('definition-unavailable',端点,'its strict definition was withdrawn and SRC fallback is forbidden')#禁止 SRC
        return 自身.解析源描述符(命名空间,方法,端点)#SRC

    def 解析源描述符(自身,命名空间,方法,端点):#从活动服务推导 SRC 描述符
        """多个服务导出同一端点则歧义。"""
        候选们=[]#候选
        属性表=getattr(自身.ctx.reflect,'属性表',None) or getattr(自身.ctx.reflect,'props',{})#属性
        for 服务键,定义 in (属性表.items() if hasattr(属性表,'items') else []):#遍历
            if (定义.get('type') if isinstance(定义,dict) else getattr(定义,'type',None))!='service':#只看服务
                continue#跳过
            接收方=自身.ctx.get(服务键)#接收方
            if not 是否对象(接收方):#非对象
                continue#跳过
            原始=取原始(接收方)#原始
            值=getattr(原始,'typertRemote',None)#绑定
            if 值 is None:#无绑定
                continue#跳过
            绑定=读绑定(值,原始,服务键,端点)#校验
            if 绑定['namespace']!=命名空间:#命名空间不匹配
                continue#跳过
            标记=None#匹配标记
            for 候选 in 远程方法们(原始):#找标记
                if (候选.get('exportName') or 候选['method'])==方法:#命中
                    标记=候选#记下
                    break#停止
            if 标记 is None:#没有
                continue#跳过
            候选们.append(自身.源描述符(绑定,标记,方法,端点))#加入
        if len(候选们)==0:#无候选
            raise 网关错误('invocation-unavailable',端点,'no active Remote method exports this endpoint')#不可用
        if len(候选们)>1:#歧义
            服务们=', '.join(sorted(候选['service'] for 候选 in 候选们))#列出
            raise 网关错误('ambiguous-endpoint',端点,'multiple active Services export this endpoint: '+服务们)#歧义
        return 候选们[0]#唯一

    def 源描述符(自身,绑定,标记,方法,端点):#由 SRC 标记拼出调用描述符
        """从签名读参数名，按 lookup 声明推导来源。"""
        名们=方法参数名(绑定['service'],标记['method'],端点)#参数名
        信号下标=名们.index('signal') if 'signal' in 名们 else -1#signal 位置
        if 信号下标>=0 and 信号下标!=len(名们)-1:#不是最后一个
            raise 网关错误('signature-invalid',端点,'SRC cancellation parameter signal must be the final parameter',{'field':'signal'})#非法
        取消={'parameter':'signal'} if 信号下标>=0 else None#取消约定
        业务名=名们 if 取消 is None else 名们[:-1]#去掉 signal
        参数们=[]#业务参数
        线路们=set()#已占用线字段
        for 名 in 业务名:#逐个
            匹配们=[声明 for 声明 in 自身.ctx.typert.lookups.definitions() if 声明['parameter']==名]#按参数名
            if len(匹配们)>1:#多匹配
                raise 网关错误('signature-invalid',端点,'parameter '+repr(名)+' matches multiple lookup providers',{'field':名})#非法
            匹配=匹配们[0] if len(匹配们)==1 else None#至多一个
            if 匹配 is None:#json
                参数={'name':名,'wire':名,'source':'json','codec':{'mode':'src-json'}}#json 参数
            else:#lookup
                参数={'name':名,'wire':匹配['wire'],'source':'lookup','lookup':匹配['key'],'codec':{'mode':'src-json'}}#lookup
            if 参数['wire'] in 线路们:#冲突
                raise 网关错误('signature-invalid',端点,'multiple parameters use wire field '+repr(参数['wire']),{'field':参数['wire']})#非法
            线路们.add(参数['wire'])#占用
            参数们.append(参数)#加入
        接收方={'kind':'direct'}#默认直接
        if 标记['invocation']['kind']=='context':#按上下文
            提供方=自身.ctx.typert.contexts.getHost(标记['invocation']['context'])#宿主 Context
            if 提供方 is None:#不可用
                raise 网关错误('context-unavailable',端点,'Context provider '+repr(标记['invocation']['context'])+' is unavailable')#抛出
            if 提供方['wire'] in 线路们:#冲突
                raise 网关错误('signature-invalid',端点,'Context identity conflicts with wire field '+repr(提供方['wire']),{'field':提供方['wire']})#非法
            接收方={'kind':'context','context':标记['invocation']['context'],'wire':提供方['wire'],'codec':{'mode':'src-json'}}#上下文调用
        描述符={#SRC 描述符
            'id':'src:'+绑定['serviceKey']+'#'+端点,#id
            'service':绑定['serviceKey'],#服务键
            'namespace':绑定['namespace'],#命名空间
            'method':方法,#导出名
            'invocation':接收方,#接收方
            'parameters':参数们,#参数
            'result':{'mode':'src-json'},#弱结果
        }#描述符
        if 标记['method']!=方法:#导出名与实现不同
            描述符['implementation']=标记['method']#记下实现
        if 取消 is not None:#有取消
            描述符['cancellation']=取消#带上
        return 描述符#描述符

    def 解析接收上下文(自身,描述符,参数,端点):#按描述符解析接收方所在上下文
        """直接调用用网关自身上下文。"""
        if 描述符['invocation']['kind']=='direct':#直接
            return 自身.ctx#自身
        调用=描述符['invocation']#上下文调用
        提供方=自身.ctx.typert.contexts.getHost(调用['context'])#提供方
        if 提供方 is None:#不可用
            raise 网关错误('context-unavailable',端点,'Context provider '+repr(调用['context'])+' is unavailable')#抛出
        if 提供方['wire']!=调用['wire'] or (调用['codec'].get('mode')=='strict' and 提供方.get('wireTypeSymbol')!=调用['codec'].get('typeSymbol')):#不匹配
            raise 网关错误('provider-mismatch',端点,'Context provider '+repr(调用['context'])+' does not match its strict definition',{'field':调用['wire']})#抛出
        身份=解码(调用['codec'],参数.get(调用['wire']),'input-invalid',端点,调用['wire'])#解码身份
        try:#解析
            上下文对象=解开(提供方['resolve'](身份))#解析
        except 查找策略失败:#查找策略失败保留
            raise#原样
        except BaseException as 原因:#其他
            raise 网关错误('context-failed',端点,'Context provider '+repr(调用['context'])+' failed',{'cause':原因,'field':调用['wire']})#包成
        if 上下文对象 is None:#未解析到
            raise 网关错误('context-not-found',端点,'Context provider '+repr(调用['context'])+' did not resolve the requested identity',{'field':调用['wire']})#抛出
        return 上下文对象#上下文

    def 解析参数(自身,参数,参数表,端点):#按描述符解析单个参数
        """缺席 json 可省略；lookup 必须出现。"""
        if 参数['wire'] not in 参数表:#缺席
            return None#undefined
        值=解码(参数['codec'],参数表[参数['wire']],'input-invalid',端点,参数['wire'])#解码
        if 参数['source']=='json':#json
            return 值#直接用
        键=参数.get('lookup')#查找键
        if 键 is None:#缺键
            raise 网关错误('lookup-unavailable',端点,'lookup parameter '+repr(参数['name'])+' has no provider key',{'field':参数['wire']})#抛出
        提供方=自身.ctx.typert.lookups.get(键)#提供方
        if 提供方 is None:#不可用
            raise 网关错误('lookup-unavailable',端点,'lookup provider '+repr(键)+' is unavailable',{'field':参数['wire']})#抛出
        if 提供方['wire']!=参数['wire'] or (参数['codec'].get('mode')=='strict' and 提供方.get('wireTypeSymbol')!=参数['codec'].get('typeSymbol')):#不匹配
            raise 网关错误('provider-mismatch',端点,'lookup provider '+repr(键)+' does not match its strict definition',{'field':参数['wire']})#抛出
        try:#解析
            已解析=解开(提供方['resolve'](值))#解析
        except 查找策略失败:#策略失败
            raise#原样
        except BaseException as 原因:#其他
            raise 网关错误('lookup-failed',端点,'lookup provider '+repr(键)+' failed',{'cause':原因,'field':参数['wire']})#包成
        if 已解析 is None:#未找到
            raise 网关错误('lookup-not-found',端点,'lookup provider '+repr(键)+' did not resolve the requested identity',{'field':参数['wire']})#抛出
        return 已解析#业务对象

TypertGatewayService=Typert网关服务#上游名

def RPC失败(错误):#把捕获错误折成 RPC 失败信封
    """取消 / 查找失败 / 内部。"""
    if isinstance(错误,远程调用已取消):#取消
        return {'ok':False,'error':{'code':'cancelled','message':str(错误),'details':{}}}#取消信封
    if isinstance(错误,查找策略失败):#查找策略
        return {'ok':False,'error':错误.failure}#沿用
    return {'ok':False,'error':{'code':'internal','message':str(错误) if isinstance(错误,BaseException) else str(错误),'details':{}}}#内部

def 校验绑定(接收方,服务键,命名空间,端点):#校验接收方上的 typertRemote 绑定
    """返回绑定与原始对象。"""
    原始=取原始(接收方)#原始
    值=getattr(原始,'typertRemote',None)#绑定
    if 值 is None:#没有
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has no visible typertRemote binding')#抛出
    return {'binding':读绑定(值,原始,服务键,端点,命名空间),'original':原始}#解析结果

def 读绑定(值,原始,服务键,端点,命名空间=None):#校验绑定对象字段
    """与接收方一致才通过。"""
    if not isinstance(值,dict) or 值.get('service') is not 原始 or 值.get('serviceKey')!=服务键 or not isinstance(值.get('namespace'),str) or (命名空间 is not None and 值.get('namespace')!=命名空间):#不一致
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has an inconsistent typertRemote binding')#抛出
    return 值#绑定

def 方法参数名(服务实例,方法,端点):#从方法签名读唯一标识符参数名
    """禁止解构、默认、剩余；用 inspect.signature。"""
    实现=None#函数实现
    for 类 in type(服务实例).__mro__:#沿 MRO
        if 方法 in 类.__dict__:#本层有
            成员=类.__dict__[方法]#取出
            if callable(成员):#可调用
                实现=成员#记下
            break#停止
    if 实现 is None:#没有
        raise 网关错误('method-unavailable',端点,'Remote marker has no prototype method '+repr(方法))#抛出
    try:#读签名
        签名=inspect.signature(实现)#签名
    except (TypeError,ValueError):#失败
        raise 网关错误('signature-invalid',端点,'SRC method '+repr(方法)+' must use unique identifier parameters without destructuring, defaults, or rest')#非法
    名们=[]#参数名
    已见=set()#查重
    for 名,参数 in 签名.parameters.items():#逐个
        if 名 in ('self','cls','自身','类'):#跳过接收者
            continue#跳过
        if 参数.kind in (inspect.Parameter.VAR_POSITIONAL,inspect.Parameter.VAR_KEYWORD):#剩余
            raise 网关错误('signature-invalid',端点,'SRC method '+repr(方法)+' must use unique identifier parameters without destructuring, defaults, or rest')#非法
        if 参数.default is not inspect.Parameter.empty:#有默认
            raise 网关错误('signature-invalid',端点,'SRC method '+repr(方法)+' must use unique identifier parameters without destructuring, defaults, or rest')#非法
        if 标识符模式.match(名) is None or 名 in 已见:#非法或重名
            raise 网关错误('signature-invalid',端点,'SRC method '+repr(方法)+' must use unique identifier parameters without destructuring, defaults, or rest')#非法
        已见.add(名)#记下
        名们.append(名)#加入
    return 名们#按出现顺序

def 断言精确参数(参数,描述符,端点):#校验 args 自有键与描述符期望完全一致
    """不符则抛 arguments-invalid。"""
    if not 是否普通对象(参数):#必须普通对象
        raise 网关错误('arguments-invalid',端点,'args must be a plain object')#抛出
    期望=set(项['wire'] for 项 in 描述符['parameters'])#业务线字段
    if 描述符['invocation']['kind']=='context':#上下文
        期望.add(描述符['invocation']['wire'])#身份线字段
    实际=set(参数.keys())#实际键
    多余=实际-期望#多余
    可缺=set(#允许缺席的 json 线字段
        项['wire'] for 项 in 描述符['parameters']
        if 项['source']=='json' and (项.get('acceptsUndefined') is True or 项['codec'].get('mode')=='src-json')
    )#可缺
    缺失=[键 for 键 in 期望 if 键 not in 参数 and 键 not in 可缺]#缺失
    if len(多余)==0 and len(缺失)==0:#完全匹配
        return#通过
    子句=[]#诊断
    if len(缺失)>0:#有缺失
        子句.append('missing '+', '.join(repr(键) for 键 in 缺失))#列出
    if len(多余)>0:#有多余
        子句.append('unexpected '+', '.join(repr(键) for 键 in 多余))#列出
    raise 网关错误('arguments-invalid',端点,'args fields do not match the descriptor: '+'; '.join(子句))#抛出

def 解码(编解码,值,码,端点,字段):#按编解码约定做边界校验
    """严格模式先走 schema；再断言 JSON 安全。"""
    try:#解析
        if 编解码.get('mode')=='strict':#严格
            值=编解码['schema'].parse(值)#schema
            if 值 is None:#undefined
                return 值#直接返回
        断言JSON值(值,set())#JSON 安全
        return 值#通过
    except BaseException as 原因:#失败
        消息=('wire field '+repr(字段)+' failed boundary validation') if 码=='input-invalid' else 'business result failed boundary validation'#诊断
        raise 网关错误(码,端点,消息,{'cause':原因,'field':字段})#包成

def 断言JSON值(值,祖先):#断言值为 JSON 安全且无环
    """null/字符串/布尔/有限数字/稠密数组/普通对象。"""
    if 值 is None or isinstance(值,(str,bool)):#简单
        return#通过
    if isinstance(值,(int,float)) and not isinstance(值,bool):#数字
        if 值==值 and 值 not in (float('inf'),float('-inf')):#有限（NaN!=NaN）
            return#通过
        raise TypeError('non-finite number is not JSON-safe')#非有限
    if not 是否对象(值):#其余原始类型
        raise TypeError(type(值).__name__+' is not JSON-safe')#不安全
    if id(值) in 祖先:#成环
        raise TypeError('cyclic value is not JSON-safe')#环
    祖先.add(id(值))#压入
    try:#递归
        if isinstance(值,(list,tuple)):#数组
            for 项 in 值:#逐项
                断言JSON值(项,祖先)#递归
            return#通过
        if not 是否普通对象(值):#非普通对象
            raise TypeError('non-plain object is not JSON-safe')#不安全
        for 键 in 值.keys():#遍历
            if not isinstance(键,str):#非字符串键
                raise TypeError('non-data property is not JSON-safe')#不安全
            断言JSON值(值[键],祖先)#递归
    finally:#弹出
        祖先.discard(id(值))#离开
