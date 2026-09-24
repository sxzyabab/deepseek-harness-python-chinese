"""通过 Cordis 服务与已注册提供方做在线 Typert Remote 分发。

传输、请求关联与响应信封属于 Connection。
"""
import inspect,re,threading#参数名、标识符与中止
from concurrent.futures import Future as 原生结果#单次操作结果
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from ...typert.协议 import 远程方法列表,远程错误,取远程错误,是否远程json值#Remote 标记与失败
from uuid import uuid4 as 生成uuid4#事件关联标识
from .流协议 import (
    远程事件流端点,远程事件结果端点,
    解析远程事件结果,投影远程事件请求,还原远程事件拒绝,
    是否远程事件智能体标识,
)
from ...工具.双端队列 import 双端队列

__all__=['网关错误','Typert网关服务','已中止','若已中止则抛出','操作任务','中止信号','中止控制器']#仅中文公开名

标识符模式=re.compile(r'^[$A-Z_a-z][$A-Za-z0-9_]*\Z')#SRC 参数名，ASCII 标识符，行尾对齐 JS $

class 网关错误(远程错误):
    """在被调业务方法之外产生的分发失败。"""
    def __init__(自身,码,端点,消息,选项=None):
        """消息中不嵌入边界值。选项为 dict。"""
        if 选项 is None:#无选项
            选项={}#空
        if not 码.startswith('gateway/'):#线路码带 gateway/ 前缀
            码='gateway/'+码#补前缀
        原因=选项['cause'] if 'cause' in 选项 else None#可选原因
        细节={'endpoint':端点}#端点
        if 'field' in 选项 and 选项['field'] is not None:#有字段
            细节['field']=选项['field']#字段
        全文='typert gateway: '+端点+': '+消息#带端点前缀
        super().__init__(码,全文,细节,原因=原因 if isinstance(原因,BaseException) else None)#构造
        自身.name='TypertGatewayError'#固定错误名
        自身.endpoint=端点#端点
        自身.field=选项['field'] if 'field' in 选项 else None#可选线字段

class 远程调用已取消(Exception):
    """Remote 调用已被取消。"""
    def __init__(自身,端点,原因):
        """记下端点与原因。"""
        super().__init__('Remote invocation "'+端点+'" was aborted')#消息
        自身.name='RemoteInvocationCancelled'#按结构识别
        自身.endpoint=端点#端点
        if isinstance(原因,BaseException):#原因已是异常
            自身.__cause__=原因#挂原因

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                包装=网关错误('internal','','task rejected')#包装拒绝
                包装.原因=错误#附加信息做成属性
                自身._未来.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

class 中止信号:
    """threading.Event 取消通道。原因用异常对象承载。"""
    def __init__(自身,已中止标志=False):
        """创建一条取消通道。"""
        自身._事件=threading.Event()#中止标志
        自身._异常=None#中止时抛出的异常
        if 已中止标志:#创建时已中止
            自身._事件.set()#置位
            自身._异常=远程调用已取消('','')#默认中止异常

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#原因已是异常
            自身._异常=原因#用异常对象承载
        elif 原因 is not None:#非异常原因
            错=远程调用已取消('','')#包装
            错.原因=原因#附加属性
            自身._异常=错#记下
        else:#无原因
            自身._异常=远程调用已取消('','')#默认
        自身._事件.set()#置位

    @staticmethod
    def 任一(信号列表):
        """最先中止的那路胜出。"""
        融合=中止控制器()#融合控制器
        for 信号 in 信号列表:#先扫已中止
            if 信号 is not None and 已中止(信号):#已中止
                融合.中止(信号._异常)#立刻胜出
                return 融合.信号#已中止的融合信号
        def 转发中止(来源):
            """等到来源置位后转发给融合控制器。"""
            来源._事件.wait()#阻塞到中止
            融合.中止(来源._异常)#转发异常
        for 信号 in 信号列表:#每路一线程
            if 信号 is None:#无信号
                continue#跳过
            工作=threading.Thread(target=转发中止,args=(信号,))#转发线程
            工作.daemon=True#不挡住退出
            工作.start()
        return 融合.信号#融合信号

class 中止控制器:
    """发出中止的控制器。"""
    def __init__(自身):
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出承载原因的异常。"""
    if 信号 is None:#无信号
        return#无信号
    if not 信号._事件.is_set():#仍活着
        return#仍活着
    if 信号._异常 is not None:#有承载异常
        raise 信号._异常#抛出
    raise 远程调用已取消('','')#默认中止

def 是否对象(值):
    """非 None 对象或函数。"""
    if 值 is None:#空
        return False#不是
    if isinstance(值,(str,bytes,bytearray,int,float,bool)):#标量
        return False#不是
    return True#对象或可调用

def 是否普通对象(值):
    """数组不是普通对象；要求 dict。"""
    return isinstance(值,dict)#普通 dict

def 拼端点(命名空间,方法):
    """返回 namespace/method。"""
    return 命名空间+'/'+方法#端点

def 取原始(接收方):
    """Python 无 Cordis 代理符号，接收方即原始对象。"""
    return 接收方#原样

class Typert网关服务(服务):
    """用严格生成定义或保守 SRC 标记，对照当前 Cordis 服务与 Typert 提供方做解析。"""
    inject=['typert']#框架槽：依赖 typert

    def __init__(自身,上下文):
        """向活动的 Typert 注册表登记网关。"""
        super().__init__(上下文,'typertGateway')#以 typertGateway 名注册
        自身.源声明=None#SRC 端点声明缓存
        自身.远程事件登记=None#唯一转发事件源
        自身.远程事件客户端={}#clientId → 客户端
        自身.待决远程事件={}#eventId → 挂起瀑布
        def 服务变更(*位置参数,**关键字参数):
            """下次认领时重新收集。"""
            自身.源声明=None#清空
        上下文.监听('internal/service',服务变更)#监听
        def 挂连接(连接上下文):
            """拦截 /api 下的远程调用。"""
            连接=连接上下文.connection#连接服务
            def 认领(端点):
                """是否认领该端点。"""
                return 自身.认领端点(端点)#委托
            def 分发(端点,载荷,信号):
                """分发一次 RPC。"""
                return 自身.分发RPC(端点,载荷,信号)#委托
            连接.rpc.intercept('/api',认领,分发,{'authority':'trusted-host'})#仅受信宿主
        上下文.依赖启动(['connection'],挂连接)#等 connection

    def 认领端点(自身,端点):
        """两端非空；严格定义/曾见或 SRC 声明命中则认领。"""
        if 端点==远程事件结果端点:#事件结果
            return True#认领
        段=端点.split('/')#拆
        if len(段)!=2 or 段[0]=='' or 段[1]=='':#非法
            return False#不认领
        if 自身.ctx.typert.local.get(端点) is not None or 自身.ctx.typert.local.hasSeen(端点):#严格或曾见
            return True#认领
        if 自身.源声明 is None:#惰性收集
            自身.源声明=自身.收集源声明()#收集
        return 端点 in 自身.源声明#SRC 命中

    def 收集源声明(自身):
        """遍历反射属性定义上的 typertRemote 绑定。"""
        声明=set()#端点集合
        反射=自身.ctx.反射#反射
        属性表=反射.属性表 if hasattr(反射,'属性表') else (反射.props if hasattr(反射,'props') else {})#属性定义
        项列表=属性表.items() if hasattr(属性表,'items') else []#迭代
        for 服务键,定义 in 项列表:#遍历
            种类=定义['type'] if isinstance(定义,dict) and 'type' in 定义 else getattr(定义,'type',None)#种类
            if 种类!='service':#只看服务
                continue#跳过
            接收方=自身.ctx.获取服务(服务键)#活动接收方
            if not 是否对象(接收方):#非对象
                continue#跳过
            原始=取原始(接收方)#原始对象
            绑定=getattr(原始,'typertRemote',None)#绑定
            if not isinstance(绑定,dict) or 'namespace' not in 绑定 or not isinstance(绑定['namespace'],str):#无效
                continue#跳过
            命名空间=绑定['namespace']#命名空间
            for 候选 in 远程方法列表(原始):#枚举 Remote 方法
                方法=候选['exportName'] if 'exportName' in 候选 and 候选['exportName'] is not None else 候选['method']#导出名或方法名
                声明.add(拼端点(命名空间,方法))#加入
        return 声明#集合

    def invoke(自身,请求):
        """通过严格生成反射或 SRC 标记调用一个在线 Remote 方法。请求为 dict。"""
        端点=拼端点(请求['namespace'],请求['method'])#拼端点
        描述符=自身.解析描述符(请求['namespace'],请求['method'],端点)#解析
        断言精确参数(请求['args'],描述符,端点)#校验 args
        接收上下文=自身.解析接收上下文(描述符,请求['args'],端点)#接收方上下文
        接收方=接收上下文.获取服务(描述符['service'])#活动服务
        if not 是否对象(接收方):#不可用
            raise 网关错误('service-unavailable',端点,'active Service '+repr(描述符['service'])+' is unavailable')#抛出
        校验绑定(接收方,描述符['service'],描述符['namespace'],端点)#校验绑定
        参数值=[]#业务参数
        for 参数 in 描述符['parameters']:#逐个
            参数值.append(自身.解析参数(参数,请求['args'],端点))#解析
        if 'cancellation' in 描述符 and 描述符['cancellation'] is not None:#感知取消
            参数值.append(请求['signal'] if 'signal' in 请求 and 请求['signal'] is not None else 中止信号())#补信号
        实现=描述符['implementation'] if 'implementation' in 描述符 and 描述符['implementation'] is not None else 描述符['method']#实际方法名
        方法=getattr(接收方,实现,None)#取实现
        if not callable(方法):#不可调用
            raise 网关错误('method-unavailable',端点,'active Service '+repr(描述符['service'])+' has no callable method '+repr(实现))#抛出
        try:
            结果=方法(*参数值)#同步调用
        except BaseException as 错误:
            信号=请求['signal'] if 'signal' in 请求 else None#取消信号
            if 已中止(信号):#载体已取消
                raise 远程调用已取消(端点,错误)#改标取消
            raise#原样抛出
        结果模式=描述符['result']['mode'] if 'mode' in 描述符['result'] else None#结果模式
        if 结果 is None and 结果模式!='strict':#弱描述符的 void
            return 结果#直接返回
        return 解码(描述符['result'],结果,'result-invalid',端点,'result')#边界校验

    def 分发RPC(自身,端点,载荷,信号):
        """转到 invokeRpc。"""
        return 自身.调用RPC(端点,载荷,信号)#委托

    def 调用RPC(自身,端点,载荷,信号):
        """成功带 value；失败折成信封。"""
        try:
            if 端点==远程事件结果端点:#事件结果
                结果=解析远程事件结果载荷(载荷)#校验
                客户端=自身.远程事件客户端.get(结果['clientId'])#代际
                if 客户端 is None:#无代际
                    raise Exception('typert gateway: Remote event result identifies no active event stream')
                自身.收取远程事件结果(客户端,结果)#结算
                return {'ok':True,'value':None}#无业务值
            段=端点.split('/')#拆端点
            if len(段)!=2 or 段[0]=='' or 段[1]=='':#非法
                raise 网关错误('invocation-unavailable',端点,'invalid Remote endpoint')#端点无效
            命名空间,方法=段[0],段[1]#拆出
            if (not 是否对象(载荷)) or (not 是否普通对象(载荷)) or list(载荷.keys())!=['args'] or (not 是否普通对象(载荷['args'])):#载荷形状
                raise 网关错误('arguments-invalid',端点,'Remote payload must contain exactly one plain-object args field')#必须恰好 args
            值=自身.invoke({'namespace':命名空间,'method':方法,'args':载荷['args'],'signal':信号})#分发
            return {'ok':True,'value':值}#成功信封
        except BaseException as 错误:
            return RPC失败(错误)#折成失败

    def 解析描述符(自身,命名空间,方法,端点):
        """有严格定义用之；曾见但已撤回禁止 SRC；否则 SRC。"""
        严格=自身.ctx.typert.local.get(端点)#严格定义
        if 严格 is not None:#有
            return 严格#用之
        if 自身.ctx.typert.local.hasSeen(端点):#曾见但撤回
            raise 网关错误('definition-unavailable',端点,'its strict definition was withdrawn and SRC fallback is forbidden')#禁止 SRC
        return 自身.解析源描述符(命名空间,方法,端点)#SRC

    def 解析源描述符(自身,命名空间,方法,端点):
        """多个服务导出同一端点则歧义。"""
        候选列表=[]#候选
        反射=自身.ctx.反射#反射
        属性表=反射.属性表 if hasattr(反射,'属性表') else (反射.props if hasattr(反射,'props') else {})#属性
        项列表=属性表.items() if hasattr(属性表,'items') else []#迭代
        for 服务键,定义 in 项列表:#遍历
            种类=定义['type'] if isinstance(定义,dict) and 'type' in 定义 else getattr(定义,'type',None)#种类
            if 种类!='service':#只看服务
                continue#跳过
            接收方=自身.ctx.获取服务(服务键)#接收方
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
            for 候选 in 远程方法列表(原始):#找标记
                导出名=候选['exportName'] if 'exportName' in 候选 and 候选['exportName'] is not None else 候选['method']#导出名或方法名
                if 导出名==方法:#命中
                    标记=候选#记下
                    break#停止
            if 标记 is None:#没有
                continue#跳过
            候选列表.append(自身.源描述符(绑定,标记,方法,端点))#加入
        if len(候选列表)==0:#无候选
            raise 网关错误('invocation-unavailable',端点,'no active Remote method exports this endpoint')#不可用
        if len(候选列表)>1:#歧义
            服务名串=', '.join(sorted(候选['service'] for 候选 in 候选列表))#列出
            raise 网关错误('ambiguous-endpoint',端点,'multiple active Services export this endpoint: '+服务名串)#歧义
        return 候选列表[0]#唯一

    def 源描述符(自身,绑定,标记,方法,端点):
        """从签名读参数名，按 lookup 声明推导来源。"""
        名列表=方法参数名(绑定['service'],标记['method'],端点)#参数名
        信号下标=名列表.index('signal') if 'signal' in 名列表 else -1#signal 位置
        if 信号下标>=0 and 信号下标!=len(名列表)-1:#不是最后一个
            raise 网关错误('signature-invalid',端点,'SRC cancellation parameter signal must be the final parameter',{'field':'signal'})#非法
        取消={'parameter':'signal'} if 信号下标>=0 else None#取消约定
        业务名=名列表 if 取消 is None else 名列表[:-1]#去掉 signal
        参数列表=[]#业务参数
        线路集合=set()#已占用线字段
        for 名 in 业务名:#逐个
            匹配列表=[声明 for 声明 in 自身.ctx.typert.lookups.definitions() if 声明['parameter']==名]#按参数名
            if len(匹配列表)>1:#多匹配
                raise 网关错误('signature-invalid',端点,'parameter '+repr(名)+' matches multiple lookup providers',{'field':名})#非法
            匹配=匹配列表[0] if len(匹配列表)==1 else None#至多一个
            if 匹配 is None:#json
                参数={'name':名,'wire':名,'source':'json','codec':{'mode':'src-json'}}#json 参数
            else:#lookup
                参数={'name':名,'wire':匹配['wire'],'source':'lookup','lookup':匹配['key'],'codec':{'mode':'src-json'}}#lookup
            if 参数['wire'] in 线路集合:#冲突
                raise 网关错误('signature-invalid',端点,'multiple parameters use wire field '+repr(参数['wire']),{'field':参数['wire']})#非法
            线路集合.add(参数['wire'])#占用
            参数列表.append(参数)#加入
        接收方={'kind':'direct'}#默认直接
        if 标记['invocation']['kind']=='context':#按上下文
            提供方=自身.ctx.typert.contexts.getHost(标记['invocation']['context'])#宿主 Context
            if 提供方 is None:#不可用
                raise 网关错误('context-unavailable',端点,'Context provider '+repr(标记['invocation']['context'])+' is unavailable')#抛出
            if 提供方['wire'] in 线路集合:#冲突
                raise 网关错误('signature-invalid',端点,'Context identity conflicts with wire field '+repr(提供方['wire']),{'field':提供方['wire']})#非法
            接收方={'kind':'context','context':标记['invocation']['context'],'wire':提供方['wire'],'codec':{'mode':'src-json'}}#上下文调用
        描述符={#SRC 描述符
            'id':'src:'+绑定['serviceKey']+'#'+端点,#id
            'service':绑定['serviceKey'],#服务键
            'namespace':绑定['namespace'],#命名空间
            'method':方法,#导出名
            'invocation':接收方,#接收方
            'parameters':参数列表,#参数
            'result':{'mode':'src-json'},#弱结果
        }#描述符
        if 标记['method']!=方法:#导出名与实现不同
            描述符['implementation']=标记['method']#记下实现
        if 取消 is not None:#有取消
            描述符['cancellation']=取消#带上
        return 描述符#描述符

    def 解析接收上下文(自身,描述符,参数,端点):
        """直接调用用网关自身上下文。参数为 dict。"""
        if 描述符['invocation']['kind']=='direct':#直接
            return 自身.ctx#自身
        调用=描述符['invocation']#上下文调用
        提供方=自身.ctx.typert.contexts.getHost(调用['context'])#提供方
        if 提供方 is None:#不可用
            raise 网关错误('context-unavailable',端点,'Context provider '+repr(调用['context'])+' is unavailable')#抛出
        严格=调用['codec']['mode']=='strict' if 'mode' in 调用['codec'] else False#严格
        符号匹配=('wireTypeSymbol' in 提供方 and 'typeSymbol' in 调用['codec'] and 提供方['wireTypeSymbol']==调用['codec']['typeSymbol'])#符号
        if 提供方['wire']!=调用['wire'] or (严格 and not 符号匹配):#不匹配
            raise 网关错误('provider-mismatch',端点,'Context provider '+repr(调用['context'])+' does not match its strict definition',{'field':调用['wire']})#抛出
        身份=解码(调用['codec'],参数[调用['wire']] if 调用['wire'] in 参数 else None,'input-invalid',端点,调用['wire'])#解码身份
        try:
            上下文=提供方['resolve'](身份)#同步解析
        except BaseException as 原因:
            if getattr(原因,'name',None)=='TypertLookupFailure':#查找策略按结构识别
                raise#原样
            raise 网关错误('context-failed',端点,'Context provider '+repr(调用['context'])+' failed',{'cause':原因,'field':调用['wire']})#包成
        if 上下文 is None:#未解析到
            raise 网关错误('context-not-found',端点,'Context provider '+repr(调用['context'])+' did not resolve the requested identity',{'field':调用['wire']})#抛出
        return 上下文#上下文

    def 解析参数(自身,参数,参数表,端点):
        """缺席 json 可省略；lookup 必须出现。参数与参数表为 dict。"""
        if 参数['wire'] not in 参数表:#缺席
            return None#省略键
        值=解码(参数['codec'],参数表[参数['wire']],'input-invalid',端点,参数['wire'])#解码
        if 参数['source']=='json':#json
            return 值#直接用
        if 'lookup' not in 参数:#缺键
            raise 网关错误('lookup-unavailable',端点,'lookup parameter '+repr(参数['name'])+' has no provider key',{'field':参数['wire']})#抛出
        键=参数['lookup']#查找键
        if 键 not in 自身.ctx.typert.lookups:#不可用
            raise 网关错误('lookup-unavailable',端点,'lookup provider '+repr(键)+' is unavailable',{'field':参数['wire']})#抛出
        提供方=自身.ctx.typert.lookups[键]#提供方
        严格=参数['codec']['mode']=='strict' if 'mode' in 参数['codec'] else False#严格
        符号匹配=('wireTypeSymbol' in 提供方 and 'typeSymbol' in 参数['codec'] and 提供方['wireTypeSymbol']==参数['codec']['typeSymbol'])#符号
        if 提供方['wire']!=参数['wire'] or (严格 and not 符号匹配):#不匹配
            raise 网关错误('provider-mismatch',端点,'lookup provider '+repr(键)+' does not match its strict definition',{'field':参数['wire']})#抛出
        try:
            已解析=提供方['resolve'](值)#同步解析
        except BaseException as 原因:
            if getattr(原因,'name',None)=='TypertLookupFailure':#查找策略按结构识别
                raise#原样
            raise 网关错误('lookup-failed',端点,'lookup provider '+repr(键)+' failed',{'cause':原因,'field':参数['wire']})#包成
        if 已解析 is None:#未找到
            raise 网关错误('lookup-not-found',端点,'lookup provider '+repr(键)+' did not resolve the requested identity',{'field':参数['wire']})#抛出
        return 已解析#业务对象

    def 登记远程事件(自身,源,宿主):
        """登记本应用选定的转发事件源。源为 (信号)->迭代器。"""
        if 自身.远程事件登记 is not None:#已有
            raise Exception('typert gateway: forwarded Remote event source is already registered')
        寿命=中止控制器()#源寿命
        流=源(寿命.信号)#打开
        完成=操作任务()#消费完成
        def 消费():
            """后台消费事件源。"""
            try:
                自身.消费远程事件(流,寿命.信号)#消费
            except BaseException as 错误:
                if 自身.远程事件登记 is None or 自身.远程事件登记['lifetime'] is not 寿命 or 已中止(寿命.信号):
                    pass#已拆除或已中止
                else:
                    自身.关闭远程事件(错误)#关闭
                    自身.远程事件登记=None#清空
                    寿命.中止(错误)#中止寿命
            finally:
                完成.兑现(None)#完成
        线=threading.Thread(target=消费,daemon=True)#消费线程
        线.start()
        登记={'lifetime':寿命,'done':完成,'host':{'home':宿主['home']}}#登记
        自身.远程事件登记=登记#记下
        def 拆除():
            """去掉本源并取消活动流。"""
            if 自身.远程事件登记 is 登记:#仍是本源
                自身.远程事件登记=None#清空
                错误=Exception('typert gateway: forwarded Remote event source was removed')
                登记['lifetime'].中止(错误)#中止
                自身.关闭远程事件(错误)#关闭
            完成.等待()#等消费结束
        return 拆除#拆除器

    def 打开远程事件(自身,载荷,信号):
        """打开一条转发事件流；载荷须为 {args:{}}。"""
        if (not 是否对象(载荷) or not 是否普通对象(载荷) or list(载荷.keys())!=['args']
                or not 是否对象(载荷['args']) or not 是否普通对象(载荷['args'])
                or len(载荷['args'])!=0):
            raise 网关错误('arguments-invalid',远程事件流端点,'forwarded Remote event stream requires an empty args object')
        登记=自身.远程事件登记#当前源
        if 登记 is None:#无源
            raise 网关错误('service-unavailable',远程事件流端点,'forwarded Remote event source is unavailable')
        寿命=中止信号.任一([信号,登记['lifetime'].信号])#合成寿命
        客户端标识=str(生成uuid4())#代际标识
        while 客户端标识 in 自身.远程事件客户端:#碰撞
            客户端标识=str(生成uuid4())#再抽
        客户端={'id':客户端标识,'queue':远程事件帧队列(),'deliveries':{}}#代际
        自身.远程事件客户端[客户端标识]=客户端#登记
        for 挂起 in list(自身.待决远程事件.values()):#已有瀑布
            自身.投递远程事件(挂起,客户端)#补投
        try:
            yield {'type':'ready','clientId':客户端标识,'host':登记['host']}#就绪
            yield from 客户端['queue'].迭代(寿命)#后续帧
        finally:
            自身.移除远程事件客户端(客户端)#摘掉

    def 消费远程事件(自身,源,信号):
        """消费应用事件源。"""
        for 派发 in 源:#逐帧
            if 已中止(信号):#中止
                if isinstance(派发,dict) and 'context' in 派发:#瀑布
                    派发['reject'](信号._异常)#拒绝
                return#停
            if isinstance(派发,dict) and 'context' in 派发:#瀑布
                自身.启动远程事件(派发)#启动
            else:
                自身.广播远程事件(派发)#广播
        if not 已中止(信号):#源自己结束
            raise Exception('typert gateway: forwarded Remote event source ended unexpectedly')

    def 广播远程事件(自身,帧):
        """向所有代际推 emit。"""
        断言远程事件帧(帧)#校验
        线={'type':'emit','event':帧['event'],'args':帧['args']}#线帧
        for 客户端 in 自身.远程事件客户端.values():#各代际
            客户端['queue'].推入(线)#推

    def 启动远程事件(自身,源):
        """把一次瀑布投递给现有代际。"""
        try:
            断言远程事件名(源)#名
            if not 是否远程事件智能体标识(源['context']['agentId']):#无身份
                raise TypeError('typert gateway: scoped Remote events require a non-empty Agent identity')
            投影=投影远程事件请求(源['request'],源['context']['subject'])#投影
            标识=str(生成uuid4())#事件标识
            while 标识 in 自身.待决远程事件:#碰撞
                标识=str(生成uuid4())#再抽
            try:
                def 释放上下文工厂():
                    """Context 拆除时取消。"""
                    def 取消():
                        """取消本瀑布。"""
                        自身.取消远程事件(挂起,Exception('typert gateway: Remote event Agent Context was released'))
                    return 取消
                释放上下文=源['context']['value'].副作用(释放上下文工厂,'api-gateway: Remote event '+repr(源['event']))
            except BaseException:
                源['resolve']({'kind':'next'})#委托本地
                return
            信号集合=[]#取消信号
            if 'signal' in 投影 and 投影['signal'] is not None:
                信号集合.append(投影['signal'])
            def 中止():
                """信号置位则取消。"""
                原因=None
                for 项 in 信号集合:
                    if 已中止(项):
                        原因=项._异常
                        break
                自身.取消远程事件(挂起,原因 if isinstance(原因,BaseException) else Exception('typert gateway: Remote event was cancelled'))
            挂起={
                'id':标识,'source':源,
                'frame':{
                    'type':'waterfall','event':源['event'],'eventId':标识,
                    'agentId':源['context']['agentId'],'request':投影['request'],
                },
                'deliveries':set(),
                'releaseContext':释放上下文,
                'releaseSignal':lambda: None,
            }
            监视=[]
            def 监视信号(来源):
                """等到来源置位。"""
                来源._事件.wait()
                中止()
            for 项 in 信号集合:
                线=threading.Thread(target=监视信号,args=(项,),daemon=True)
                线.start()
                监视.append(线)
            def 释放信号():
                """监视线程随取消自然结束。"""
                return None
            挂起['releaseSignal']=释放信号
            自身.待决远程事件[标识]=挂起#记下
            if any(已中止(项) for 项 in 信号集合):#已中止
                中止()
            else:
                for 客户端 in 自身.远程事件客户端.values():#投递
                    自身.投递远程事件(挂起,客户端)
        except BaseException as 错误:
            源['reject'](错误)#拒绝源

    def 投递远程事件(自身,挂起,客户端):
        """把瀑布帧推给一代。"""
        挂起['deliveries'].add(id(客户端))
        客户端['deliveries'][挂起['id']]=挂起
        客户端['queue'].推入(挂起['frame'])

    def 收取远程事件结果(自身,客户端,结果):
        """结算一次客户端瀑布结果。"""
        挂起=自身.待决远程事件.get(结果['eventId'])
        if 挂起 is None or id(客户端) not in 挂起['deliveries']:
            return
        自身.移除远程事件投递(挂起,客户端)
        结局=结果['outcome']
        if 结局['kind']=='result':
            自身.结算远程事件(挂起,{'kind':'result','value':结局.get('value')})
        elif 结局['kind']=='rejected':
            自身.取消远程事件(挂起,还原远程事件拒绝(结局['error']))
        elif len(挂起['deliveries'])==0:
            自身.结算远程事件(挂起,{'kind':'next'})

    def 移除远程事件投递(自身,挂起,客户端):
        """摘掉一代对某瀑布的投递。"""
        挂起['deliveries'].discard(id(客户端))
        客户端['deliveries'].pop(挂起['id'],None)

    def 移除远程事件客户端(自身,客户端):
        """代际结束。"""
        自身.远程事件客户端.pop(客户端['id'],None)
        for 挂起 in list(客户端['deliveries'].values()):
            自身.移除远程事件投递(挂起,客户端)
        客户端['queue'].结束()

    def 结算远程事件(自身,挂起,结局):
        """兑现源监听。"""
        自身.结束远程事件(挂起)
        挂起['source']['resolve'](结局)

    def 取消远程事件(自身,挂起,原因):
        """拒绝源监听。"""
        if 自身.待决远程事件.get(挂起['id']) is not 挂起:
            return
        自身.结束远程事件(挂起)
        挂起['source']['reject'](原因)

    def 结束远程事件(自身,挂起):
        """摘掉挂起并通知各代际取消。"""
        自身.待决远程事件.pop(挂起['id'],None)
        挂起['releaseSignal']()
        挂起['releaseContext']()
        客户端表=[]
        for 客户端 in 自身.远程事件客户端.values():
            if 挂起['id'] in 客户端['deliveries']:
                客户端表.append(客户端)
        for 客户端 in 客户端表:
            自身.移除远程事件投递(挂起,客户端)
        取消帧={'type':'cancel','eventId':挂起['id']}
        for 客户端 in 客户端表:
            客户端['queue'].推入(取消帧)

    def 关闭远程事件(自身,原因):
        """源拆除时拒绝全部挂起。"""
        for 挂起 in list(自身.待决远程事件.values()):
            自身.取消远程事件(挂起,原因)
        for 客户端 in list(自身.远程事件客户端.values()):
            客户端['queue'].结束()

def RPC失败(错误):
    """把捕获错误折成 RPC 失败信封。控制流按 name/failure 结构识别。"""
    远程=取远程错误(错误)
    if 远程 is not None:
        return {'ok':False,'error':{'code':远程.code,'message':远程.message,'details':远程.details}}
    if getattr(错误,'name',None)=='RemoteInvocationCancelled':#取消
        return {'ok':False,'error':{'code':'gateway/cancelled','message':str(错误),'details':{}}}#取消信封
    if getattr(错误,'name',None)=='TypertLookupFailure' and hasattr(错误,'failure'):#查找策略
        return {'ok':False,'error':错误.failure}#沿用
    return {'ok':False,'error':{'code':'gateway/internal','message':str(错误),'details':{}}}#内部

class 远程事件帧队列:
    """一代客户端的拉取队列。"""

    def __init__(自身):
        """空队列。"""
        自身.帧=双端队列()
        自身.等待事件=threading.Event()
        自身.已关闭=False

    def 推入(自身,帧):
        """入队。"""
        if 自身.已关闭:
            return
        自身.帧.尾推(帧)
        自身.等待事件.set()

    def 结束(自身):
        """关闭。"""
        if 自身.已关闭:
            return
        自身.已关闭=True
        自身.等待事件.set()

    def 迭代(自身,信号):
        """拉取直至关闭或中止。"""
        try:
            while True:
                while 自身.帧.大小>0:
                    yield 自身.帧.头弹()
                if 自身.已关闭 or 已中止(信号):
                    return
                自身.等待事件.clear()
                while not 自身.已关闭 and not 已中止(信号) and 自身.帧.大小==0:
                    自身.等待事件.wait(0.05)
        finally:
            pass

def 断言远程事件帧(帧):
    """校验 emit 帧。"""
    断言远程事件名(帧)
    if not isinstance(帧.get('args'),list) or not 是否远程json值(帧['args']):
        raise TypeError('typert gateway: Remote event '+repr(帧.get('event'))+' arguments are not lossless JSON data')

def 断言远程事件名(帧):
    """事件名非空。"""
    if not isinstance(帧.get('event'),str) or 帧.get('event')=='':
        raise TypeError('typert gateway: Remote event name must be a nonempty string')

def 解析远程事件结果载荷(载荷):
    """载荷须恰好 args。"""
    if (not 是否对象(载荷) or not 是否普通对象(载荷)
            or list(载荷.keys())!=['args']):
        raise Exception('typert gateway: Remote event result requires exactly one plain-object args field')
    return 解析远程事件结果(载荷['args'])

def 校验绑定(接收方,服务键,命名空间,端点):
    """返回绑定与原始对象。"""
    原始=取原始(接收方)#原始
    值=getattr(原始,'typertRemote',None)#绑定
    if 值 is None:#没有
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has no visible typertRemote binding')#抛出
    return {'binding':读绑定(值,原始,服务键,端点,命名空间),'original':原始}#解析结果

def 读绑定(值,原始,服务键,端点,命名空间=None):
    """与接收方一致才通过。值为 dict。"""
    if not isinstance(值,dict):#非映射
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has an inconsistent typertRemote binding')#抛出
    if ('service' not in 值) or (值['service'] is not 原始):#服务不是同一对象
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has an inconsistent typertRemote binding')#抛出
    if ('serviceKey' not in 值) or 值['serviceKey']!=服务键:#键不符
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has an inconsistent typertRemote binding')#抛出
    if ('namespace' not in 值) or (not isinstance(值['namespace'],str)):#命名空间非法
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has an inconsistent typertRemote binding')#抛出
    if 命名空间 is not None and 值['namespace']!=命名空间:#命名空间不符
        raise 网关错误('binding-invalid',端点,'Service '+repr(服务键)+' has an inconsistent typertRemote binding')#抛出
    return 值#绑定

def 方法参数名(服务实例,方法,端点):
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
    try:
        签名=inspect.signature(实现)#签名
    except (TypeError,ValueError):
        raise 网关错误('signature-invalid',端点,'SRC method '+repr(方法)+' must use unique identifier parameters without destructuring, defaults, or rest')#非法
    名列表=[]#参数名
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
        名列表.append(名)#加入
    return 名列表#按出现顺序

def 断言精确参数(参数,描述符,端点):
    """校验 args 自有键与描述符期望完全一致。参数为 dict。"""
    if not 是否普通对象(参数):#必须普通对象
        raise 网关错误('arguments-invalid',端点,'args must be a plain object')#抛出
    期望=set(项['wire'] for 项 in 描述符['parameters'])#业务线字段
    if 描述符['invocation']['kind']=='context':#上下文
        期望.add(描述符['invocation']['wire'])#身份线字段
    实际=set(参数.keys())#实际键
    多余=实际-期望#多余
    可缺=set()#允许缺席的 json 线字段
    for 项 in 描述符['parameters']:#逐个
        接受省略=('acceptsUndefined' in 项 and 项['acceptsUndefined'] is True) or ('mode' in 项['codec'] and 项['codec']['mode']=='src-json')#可缺
        if 项['source']=='json' and 接受省略:#可缺
            可缺.add(项['wire'])#记下
    缺失=[键 for 键 in 期望 if 键 not in 参数 and 键 not in 可缺]#缺失
    if len(多余)==0 and len(缺失)==0:#完全匹配
        return#通过
    子句=[]#诊断
    if len(缺失)>0:#有缺失
        子句.append('missing '+', '.join(repr(键) for 键 in 缺失))#列出
    if len(多余)>0:#有多余
        子句.append('unexpected '+', '.join(repr(键) for 键 in 多余))#列出
    raise 网关错误('arguments-invalid',端点,'args fields do not match the descriptor: '+'; '.join(子句))#抛出

def 解码(编解码,值,码,端点,字段):
    """严格模式先走 schema；再断言 JSON 安全。编解码为 dict。"""
    try:
        if 'mode' in 编解码 and 编解码['mode']=='strict':#严格
            值=编解码['schema'].parse(值)#schema
            if 值 is None:#undefined
                return 值#直接返回
        断言JSON值(值,set())#JSON 安全
        return 值#通过
    except BaseException as 原因:
        消息=('wire field '+repr(字段)+' failed boundary validation') if 码=='input-invalid' else 'business result failed boundary validation'#诊断
        raise 网关错误(码,端点,消息,{'cause':原因,'field':字段})#包成

def 断言JSON值(值,祖先):
    """null/字符串/布尔/有限数字/稠密数组/普通对象。"""
    if 值 is None or isinstance(值,(str,bool)):#简单
        return#通过
    if isinstance(值,(int,float)) and not isinstance(值,bool):#数字，先排除 bool
        if 值==值 and 值 not in (float('inf'),float('-inf')):#有限（NaN!=NaN）
            return#通过
        raise TypeError('non-finite number is not JSON-safe')#非有限
    if not 是否对象(值):#其余原始类型
        raise TypeError(type(值).__name__+' is not JSON-safe')#不安全
    if id(值) in 祖先:#成环
        raise TypeError('cyclic value is not JSON-safe')#环
    祖先.add(id(值))#压入
    try:
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
    finally:
        祖先.discard(id(值))#离开
