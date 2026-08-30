"""生成的 Typert 反射、Remote 调用、以及依赖倒置的 lookup/Context 提供方的运行时注册表。

对齐上游 `typert/registry/src/service.ts`。公开面仅中文名。不做 TypeScript 分析，也不生成模式。
"""
import re#端点段校验
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from ..协议 import 是否合法远程段#Remote 段校验

__all__=[#仅中文公开名
    '拼模式键','拼包面键','拼端点','Typert注册表','TypertRegistry',
]#公开面结束

端点段模式=re.compile(r'^[A-Za-z0-9_$.-]+$')#RPC 端点段

def 拼模式键(包名,名):#组合包名与模式名
    """拼出一条生成模式的全局键 `<package>#<name>`。"""
    return 包名+'#'+名#全局模式键

def 拼包面键(包名,面):#组合包名与面
    """拼出一份包-面模型的身份 `<package>#<face>`。"""
    return 包名+'#'+面#包-面键

def 拼端点(描述符):#组合命名空间与方法
    """拼出本地与 Remote 调用注册表使用的端点键 `<namespace>/<method>`。"""
    return 描述符['namespace']+'/'+描述符['method']#端点键

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 校验非空(主语,值):#校验非空字符串
    """空串则抛。"""
    if len(值)==0:#空
        raise Exception('typert: invalid '+主语+' — must be nonempty')#拒绝

def 校验段(主语,值):#校验非空且不含 #
    """空或含 # 则抛。"""
    if len(值)==0 or '#' in 值:#非法
        raise Exception('typert: invalid '+主语+' "'+值+'" — must be nonempty and must not contain "#"')#拒绝

def 校验线路名(主语,值):#校验 RPC 端点段字符
    """点段或非法字符则抛。"""
    if 值=='.' or 值=='..' or 端点段模式.match(值) is None:#非法
        raise Exception('typert: invalid '+主语+' "'+值+'" — must contain only RPC endpoint segment characters')#拒绝

def 校验编解码(编解码,主语):#校验一条编解码声明
    """弱 JSON 模式直接通过；严格模式要有类型符号与 parse。"""
    if 编解码.get('mode')=='src-json':#弱模式
        return#通过
    校验非空(主语+' type symbol',编解码.get('typeSymbol') or '')#类型符号
    模式=编解码.get('schema')#模式实例
    if 模式 is None or not callable(getattr(模式,'parse',None)):#无 parse
        raise Exception('typert: '+主语+' strict codec has no parse() method')#拒绝

def 校验调用(描述符):#校验一条调用描述符
    """校验 id/服务/命名空间/方法/参数/作用域/接收方。"""
    校验非空('invocation id',描述符['id'])#调用 id
    校验段('invocation service key',描述符['service'])#服务键
    校验线路名('invocation namespace',描述符['namespace'])#命名空间
    校验线路名('invocation method',描述符['method'])#方法名
    if 描述符.get('implementation') is not None:#有实现别名
        校验线路名('invocation implementation method',描述符['implementation'])#实现名
    校验编解码(描述符['result'],描述符['id']+' result')#结果编解码
    线路们=set()#已见线路字段
    for 参数 in 描述符['parameters']:#逐个业务参数
        校验线路名('parameter name',参数['name'])#参数名
        校验线路名('parameter wire field',参数['wire'])#线路字段
        if 参数['wire'] in 线路们:#重复
            raise Exception('typert: invocation "'+描述符['id']+'" repeats wire field "'+参数['wire']+'"')#拒绝
        线路们.add(参数['wire'])#记下
        if 参数['source']=='lookup':#lookup 参数
            if 参数.get('acceptsUndefined') is not None:#lookup 不能接受 undefined
                raise Exception('typert: invocation "'+描述符['id']+'" lookup parameter "'+参数['name']+'" cannot accept undefined')#拒绝
            if 参数.get('lookup') is None:#缺少 lookup 键
                raise Exception('typert: invocation "'+描述符['id']+'" lookup parameter "'+参数['name']+'" has no lookup key')#拒绝
            校验段('lookup key',参数['lookup'])#校验键
        elif 参数.get('lookup') is not None:#JSON 却带 lookup
            raise Exception('typert: invocation "'+描述符['id']+'" JSON parameter "'+参数['name']+'" declares a lookup key')#拒绝
        校验编解码(参数['codec'],描述符['id']+' parameter '+参数['name'])#参数编解码
    取消=描述符.get('cancellation')#取消声明
    if 取消 is not None and 取消.get('parameter')!='signal':#必须是 signal
        raise Exception('typert: invocation "'+描述符['id']+'" cancellation parameter must be "signal"')#拒绝
    if 描述符.get('scope') is not None:#直接作用域投影
        if 描述符['invocation']['kind']!='direct':#Context 接收者不能再声明
            raise Exception('typert: invocation "'+描述符['id']+'" Context receiver cannot declare a direct scope projection')#拒绝
        校验段('scope Context key',描述符['scope']['context'])#作用域 Context
        校验线路名('scope wire field',描述符['scope']['wire'])#作用域线路
        查找们=[候选 for 候选 in 描述符['parameters'] if 候选['source']=='lookup']#lookup 参数
        参数=查找们[0] if len(查找们)==1 else None#必须恰好一个
        if 参数 is None or 参数['wire']!=描述符['scope']['wire'] or 参数.get('lookup')!=描述符['scope']['context']:#不对齐
            raise Exception('typert: invocation "'+描述符['id']+'" scope wire "'+描述符['scope']['wire']+'" must select its only lookup parameter')#拒绝
    if 描述符['invocation']['kind']=='context':#Context 接收者
        校验段('Context key',描述符['invocation']['context'])#Context 键
        校验线路名('Context wire field',描述符['invocation']['wire'])#Context 线路
        if 描述符['invocation']['wire'] in 线路们:#与参数冲突
            raise Exception('typert: invocation "'+描述符['id']+'" repeats wire field "'+描述符['invocation']['wire']+'"')#拒绝
        校验编解码(描述符['invocation']['codec'],描述符['id']+' Context')#身份编解码

def 查找声明相等(左,右):#比较两条 lookup 线路声明
    """四字段全等。"""
    return 左['parameter']==右['parameter'] and 左['wire']==右['wire'] and 左['hostTypeSymbol']==右['hostTypeSymbol'] and 左['wireTypeSymbol']==右['wireTypeSymbol']#全等

def 匹配过滤(记录,过滤):#记录是否匹配过滤
    """未指定包/面则放行。"""
    if 过滤.get('package') is not None and 记录['package']!=过滤['package']:#包不匹配
        return False#否
    if 过滤.get('face') is not None and 记录['face']!=过滤['face']:#面不匹配
        return False#否
    return True#是

class 变更源:#注册表变更源
    """向当前监听器广播变更。"""
    def __init__(自身,报告):#记下观察者失败报告函数
        """构造。"""
        自身.报告=报告#报告函数
        自身.监听器们=set()#当前订阅者

    def 订阅(自身,上下文,监听器):#按调用方 fiber 订阅
        """用 effect 绑定订阅生命周期。"""
        监听器们=自身.监听器们#集合
        def 生命周期():#effect 体
            """加入并在拆除时移除。"""
            监听器们.add(监听器)#加入
            yield lambda:监听器们.discard(监听器)#拆除
        return 上下文.effect(生命周期,'typert registry subscription')#登记

    def 发出(自身,变更):#向当前监听器广播
        """隔离单个监听器失败。"""
        for 监听器 in list(自身.监听器们):#快照迭代
            try:#隔离
                监听器(变更)#投递
            except BaseException as 错误:#监听器抛错
                自身.报告(变更,错误)#报告

class 描述符仓:#本地或 Remote 描述符存储
    """按端点与调用 id 存放描述符。"""
    def __init__(自身,种类,报告):#构造
        """创建变更源。"""
        自身.种类=种类#local|remote
        自身.条目={}#端点 → 条目
        自身.标识们={}#调用 id → 条目
        自身.历史=set()#本生命周期见过的端点
        自身.变更=变更源(报告)#变更源

    def 校验(自身,描述符们):#校验一批可否提交
        """端点与 id 不得与本批或已注册冲突。"""
        端点们=set()#本批端点
        标识们=set()#本批 id
        for 描述符 in 描述符们:#逐条
            校验调用(描述符)#单条校验
            端点=拼端点(描述符)#端点键
            if 端点 in 端点们 or 端点 in 自身.条目:#冲突
                raise Exception('typert: '+自身.种类+' endpoint "'+端点+'" is already registered')#拒绝
            if 描述符['id'] in 标识们 or 描述符['id'] in 自身.标识们:#id 冲突
                raise Exception('typert: '+自身.种类+' invocation id "'+描述符['id']+'" is already registered')#拒绝
            端点们.add(端点)#记下
            标识们.add(描述符['id'])#记下

    def 提交(自身,拥有者,描述符们):#提交一批
        """先写入再广播。"""
        for 描述符 in 描述符们:#写入
            条目={'descriptor':描述符,'owner':拥有者}#条目
            端点=拼端点(描述符)#端点
            自身.条目[端点]=条目#按端点
            自身.标识们[描述符['id']]=条目#按 id
            自身.历史.add(端点)#记入曾见
        for 描述符 in 描述符们:#广播
            自身.变更.发出({'kind':自身.种类,'key':拼端点(描述符)})#按端点

    def 撤回(自身,拥有者,描述符们):#按拥有者撤回
        """非本拥有者则跳过。"""
        已移除=[]#实际移除的端点
        for 描述符 in 描述符们:#逐条
            端点=拼端点(描述符)#端点
            条目=自身.条目.get(端点)#当前
            if 条目 is None or 条目['owner'] is not 拥有者:#不是本拥有者
                continue#跳过
            del 自身.条目[端点]#删端点
            if 自身.标识们.get(描述符['id']) is 条目:#同步 id
                del 自身.标识们[描述符['id']]#删 id
            已移除.append(端点)#记下
        for 端点 in 已移除:#广播
            自身.变更.发出({'kind':自身.种类,'key':端点})#变更

    def 取(自身,端点):#按端点取描述符
        """缺席为 None。"""
        条目=自身.条目.get(端点)#条目
        return None if 条目 is None else 条目['descriptor']#描述符

    def 曾见(自身,端点):#本生命周期是否见过
        """即使已撤回也返回 True。"""
        return 端点 in 自身.历史#曾见

    def 列出(自身):#按注册顺序快照
        """抽出描述符。"""
        return [条目['descriptor'] for 条目 in 自身.条目.values()]#列表

    def 订阅(自身,上下文,监听器):#订阅描述符变更
        """委托给变更源。"""
        return 自身.变更.订阅(上下文,监听器)#订阅

class 远程仓:#Remote 贡献存储
    """按包名登记 Remote 贡献。"""
    def __init__(自身,描述符仓实例):#持有描述符仓
        """构造。"""
        自身.描述符们=描述符仓实例#描述符仓
        自身.包们={}#包名 → 拥有者

    def 视图(自身,上下文):#绑定到调用方 fiber 的注册表面
        """组装 Remote 注册表视图。"""
        return {#视图
            'register':lambda 贡献:自身.登记(上下文,贡献),#登记
            'get':自身.描述符们.取,#按端点
            'list':自身.描述符们.列出,#列出
            'subscribe':lambda 监听器:自身.描述符们.订阅(上下文,监听器),#订阅
        }#视图

    def 登记(自身,上下文,贡献):#按 fiber 登记一份 Remote 贡献
        """同包已登记则拒绝。"""
        校验段('Remote package name',贡献['package'])#包名
        if 贡献['package'] in 自身.包们:#已登记
            raise Exception('typert: Remote package "'+贡献['package']+'" is already registered')#拒绝
        自身.描述符们.校验(贡献['descriptors'])#先校验
        拥有者={}#本 effect 身份
        包们=自身.包们#闭包
        描述符们=自身.描述符们#闭包
        包名=贡献['package']#包名
        描述符列表=贡献['descriptors']#描述符
        def 生命周期():#effect
            """提交并在拆除时撤回。"""
            包们[包名]=拥有者#记下
            描述符们.提交(拥有者,描述符列表)#提交
            def 拆除():#拆除
                """按拥有者删包并撤回。"""
                if 包们.get(包名) is 拥有者:#仍是本拥有者
                    del 包们[包名]#删包
                描述符们.撤回(拥有者,描述符列表)#撤回
            yield 拆除#拆除回调
        return 上下文.effect(生命周期,'typert.remotes.register('+repr(包名)+')')#登记

class 查找仓:#lookup 提供方存储
    """lookup 提供方与覆盖解析器。"""
    def __init__(自身,报告):#构造
        """创建变更源。"""
        自身.提供方们={}#键 → 条目
        自身.解析器们={}#键 → 覆盖条目
        自身.声明们={}#键 → 稳定线路声明
        自身.变更=变更源(报告)#变更源

    def 视图(自身,上下文):#绑定到调用方 fiber
        """组装 lookup 面。"""
        return {#视图
            'register':lambda 键,提供方:自身.登记(上下文,键,提供方),#登记
            'configure':lambda 键,解析器:自身.配置(上下文,键,解析器),#覆盖
            'get':自身.取,#按键
            'definitions':lambda:list(自身.声明们.values()),#声明
            'keys':lambda:list(自身.提供方们.keys()),#键
            'subscribe':lambda 监听器:自身.变更.订阅(上下文,监听器),#订阅
        }#视图

    def 取(自身,键):#按键取提供方，可能套上覆盖
        """无提供方则 None。"""
        条目=自身.提供方们.get(键)#默认
        if 条目 is None:#无
            return None#缺席
        提供方=条目['provider']#默认提供方
        覆盖=自身.解析器们.get(键)#覆盖
        if 覆盖 is None:#无覆盖
            return 提供方#默认
        return {#覆盖视图
            'parameter':提供方['parameter'],#源参数名
            'wire':提供方['wire'],#线路字段
            'hostTypeSymbol':提供方['hostTypeSymbol'],#宿主类型符号
            'wireTypeSymbol':提供方['wireTypeSymbol'],#线路类型符号
            'resolve':覆盖['provider']['resolve'],#覆盖解析
        }#视图

    def 配置(自身,上下文,键,解析器):#安装覆盖解析器
        """重复配置则拒绝。"""
        校验段('lookup key',键)#键
        if 键 in 自身.解析器们:#已配置
            raise Exception('typert: lookup "'+键+'" resolver is already configured')#拒绝
        拥有者={}#身份
        条目={'provider':{'resolve':lambda 标识:解开(解析器(标识))},'owner':拥有者}#覆盖条目
        解析器们=自身.解析器们#闭包
        变更=自身.变更#闭包
        def 生命周期():#effect
            """写入覆盖并在拆除时恢复。"""
            解析器们[键]=条目#写入
            变更.发出({'kind':'lookup','key':键})#广播
            def 拆除():#拆除
                """恢复默认。"""
                if 解析器们.get(键) is not 条目:#不是本条目
                    return#不拆
                del 解析器们[键]#删除
                变更.发出({'kind':'lookup','key':键})#广播
            yield 拆除#拆除
        return 上下文.effect(生命周期,'typert.lookups.configure('+repr(键)+')')#登记

    def 登记(自身,上下文,键,提供方):#登记 lookup 提供方
        """声明在本生命周期内必须稳定。"""
        校验段('lookup key',键)#键
        校验段('lookup parameter',提供方['parameter'])#源参数名
        校验线路名('lookup wire field',提供方['wire'])#线路字段
        校验非空('lookup Host type symbol',提供方['hostTypeSymbol'])#宿主类型符号
        校验非空('lookup wire type symbol',提供方['wireTypeSymbol'])#线路类型符号
        if 键 in 自身.提供方们:#已登记
            raise Exception('typert: lookup "'+键+'" is already registered')#拒绝
        声明={'key':键,'parameter':提供方['parameter'],'wire':提供方['wire'],'hostTypeSymbol':提供方['hostTypeSymbol'],'wireTypeSymbol':提供方['wireTypeSymbol']}#稳定声明
        已知=自身.声明们.get(键)#先前
        if 已知 is not None and not 查找声明相等(已知,声明):#声明改变
            raise Exception('typert: lookup "'+键+'" changed its wire declaration during this registry lifetime')#拒绝
        拥有者={}#身份
        条目={'provider':提供方,'owner':拥有者}#条目
        声明们=自身.声明们#闭包
        提供方们=自身.提供方们#闭包
        变更=自身.变更#闭包
        def 生命周期():#effect
            """写入提供方；拆除时撤回提供方，声明保留。"""
            声明们[键]=声明#记下声明
            提供方们[键]=条目#写入
            变更.发出({'kind':'lookup','key':键})#广播
            def 拆除():#拆除
                """撤回提供方。"""
                if 提供方们.get(键) is not 条目:#不是本条目
                    return#不拆
                del 提供方们[键]#删除
                变更.发出({'kind':'lookup','key':键})#广播
            yield 拆除#拆除
        return 上下文.effect(生命周期,'typert.lookups.register('+repr(键)+')')#登记

class 上下文仓:#宿主 Context 提供方与客户端绑定器存储
    """宿主与客户端 Context 注册。"""
    def __init__(自身,报告):#构造
        """创建变更源。"""
        自身.宿主们={}#键 → 宿主提供方
        自身.宿主解析器们={}#键 → 覆盖
        自身.客户端们={}#键 → 客户端绑定器
        自身.变更=变更源(报告)#变更源

    def 视图(自身,上下文):#绑定到调用方 fiber
        """组装 Context 面。"""
        return {#视图
            'registerHost':lambda 键,提供方:自身.登记宿主(上下文,键,提供方),#宿主
            'configureHost':lambda 键,解析器:自身.配置宿主(上下文,键,解析器),#覆盖宿主
            'registerClient':lambda 键,绑定器:自身.登记客户端(上下文,键,绑定器),#客户端
            'getHost':自身.取宿主,#取宿主
            'getClient':lambda 键:(None if 自身.客户端们.get(键) is None else 自身.客户端们[键]['provider']),#取客户端
            'subscribe':lambda 监听器:自身.变更.订阅(上下文,监听器),#订阅
        }#视图

    def 取宿主(自身,键):#按键取宿主提供方
        """可能套上覆盖解析器。"""
        条目=自身.宿主们.get(键)#默认
        if 条目 is None:#无
            return None#缺席
        提供方=条目['provider']#默认
        覆盖=自身.宿主解析器们.get(键)#覆盖
        if 覆盖 is None:#无覆盖
            return 提供方#默认
        return {'wire':提供方['wire'],'wireTypeSymbol':提供方['wireTypeSymbol'],'resolve':覆盖['provider']['resolve']}#覆盖视图

    def 配置宿主(自身,上下文,键,解析器):#安装宿主覆盖解析器
        """重复配置则拒绝。"""
        校验段('Context key',键)#键
        if 键 in 自身.宿主解析器们:#已配置
            raise Exception('typert: host-context "'+键+'" resolver is already configured')#拒绝
        条目={'provider':{'resolve':lambda 标识:解开(解析器(标识))},'owner':{}}#覆盖条目
        宿主解析器们=自身.宿主解析器们#闭包
        变更=自身.变更#闭包
        def 生命周期():#effect
            """写入覆盖。"""
            宿主解析器们[键]=条目#写入
            变更.发出({'kind':'host-context','key':键})#广播
            def 拆除():#拆除
                """恢复默认。"""
                if 宿主解析器们.get(键) is not 条目:#不是本条目
                    return#不拆
                del 宿主解析器们[键]#删除
                变更.发出({'kind':'host-context','key':键})#广播
            yield 拆除#拆除
        return 上下文.effect(生命周期,'typert.contexts.configureHost('+repr(键)+')')#登记

    def 登记宿主(自身,上下文,键,提供方):#登记宿主 Context 提供方
        """校验线路后写入宿主表。"""
        校验段('Context key',键)#键
        校验线路名('Context wire field',提供方['wire'])#线路
        校验非空('Context wire type symbol',提供方['wireTypeSymbol'])#类型符号
        return 自身.登记提供方(上下文,自身.宿主们,'host-context',键,提供方)#写入

    def 登记客户端(自身,上下文,键,绑定器):#登记客户端 Context 绑定器
        """写入客户端表。"""
        校验段('Context key',键)#键
        return 自身.登记提供方(上下文,自身.客户端们,'client-context',键,绑定器)#写入

    def 登记提供方(自身,上下文,表,种类,键,提供方):#把提供方按 fiber 写入指定表
        """重复则拒绝。"""
        if 键 in 表:#已登记
            raise Exception('typert: '+种类+' provider "'+键+'" is already registered')#拒绝
        条目={'provider':提供方,'owner':{}}#条目
        变更=自身.变更#闭包
        def 生命周期():#effect
            """写入并在拆除时撤回。"""
            表[键]=条目#写入
            变更.发出({'kind':种类,'key':键})#广播
            def 拆除():#拆除
                """撤回。"""
                if 表.get(键) is not 条目:#不是本条目
                    return#不拆
                del 表[键]#删除
                变更.发出({'kind':种类,'key':键})#广播
            yield 拆除#拆除
        return 上下文.effect(生命周期,'typert.contexts.register('+repr(键)+')')#登记

class Typert注册表(服务):#Typert 运行时注册表服务
    """生成模式、包反射、调用定义与 Remote 依赖提供方的注册表。"""
    def __init__(自身,上下文):#在给定上下文上注册 typert 服务
        """构造各仓。"""
        super().__init__(上下文,'typert')#以 typert 名注册
        def 报告(变更,错误):#观察者失败时写警告
            """警告哪个键的观察者失败。"""
            上下文.logger.warn('typert: '+变更['kind']+' observer for "'+变更['key']+'" failed')#警告
            上下文.logger.warn(错误)#原始错误
        自身.模式们={}#全局键 → 模式记录
        自身.包们={}#包-面键 → 包记录
        自身.本地仓=描述符仓('local',报告)#本地描述符
        自身.远程仓=远程仓(描述符仓('remote',报告))#Remote
        自身.查找仓=查找仓(报告)#lookup
        自身.上下文仓=上下文仓(报告)#Context

    @property
    def local(自身):#本地调用注册表面
        """当前环境的调用定义。"""
        上下文=自身.ctx#捕获
        return {#视图
            'get':自身.本地仓.取,#按端点
            'hasSeen':自身.本地仓.曾见,#曾见
            'list':自身.本地仓.列出,#列出
            'subscribe':lambda 监听器:自身.本地仓.订阅(上下文,监听器),#订阅
        }#视图

    @property
    def remotes(自身):#Remote 注册表面
        """消费方选定的 Remote 定义。"""
        return 自身.远程仓.视图(自身.ctx)#绑定

    @property
    def lookups(自身):#lookup 注册表面
        """宿主对象 lookup 提供方。"""
        return 自身.查找仓.视图(自身.ctx)#绑定

    @property
    def contexts(自身):#Context 注册表面
        """宿主 Context 提供方与客户端 Context 绑定器。"""
        return 自身.上下文仓.视图(自身.ctx)#绑定

    def register(自身,贡献):#原子登记一份贡献
        """重复的包-面身份、模式、调用 id 或端点会使整批拒绝。"""
        包记录=自身.校验包(贡献)#包记录
        模式记录们=自身.校验模式(贡献)#模式记录
        调用们=贡献['invocations']#宿主调用
        自身.本地仓.校验(调用们)#先校验
        拥有者={}#身份
        模式们=自身.模式们#闭包
        包们=自身.包们#闭包
        本地仓=自身.本地仓#闭包
        def 生命周期():#effect
            """写入整批并在拆除时撤回。"""
            包们[包记录['key']]=包记录#写包
            for 记录 in 模式记录们:#写模式
                模式们[记录['key']]=记录#写入
            本地仓.提交(拥有者,调用们)#提交调用
            def 拆除():#拆除
                """整批撤回。"""
                if 包们.get(包记录['key']) is 包记录:#仍是本拥有者
                    del 包们[包记录['key']]#删包
                for 记录 in 模式记录们:#删模式
                    if 模式们.get(记录['key']) is 记录:#仍是本记录
                        del 模式们[记录['key']]#删除
                本地仓.撤回(拥有者,调用们)#撤回调用
            yield 拆除#拆除
        return 自身.ctx.effect(生命周期,'typert.register()')#登记

    def get(自身,键):#按全局键取模式记录
        """缺席为 None。"""
        return 自身.模式们.get(键)#记录

    def resolve(自身,键):#解析必需模式，缺席则抛
        """键畸形、包面缺席、或该模式未被贡献时抛出。"""
        记录=自身.模式们.get(键)#查找
        if 记录 is not None:#命中
            return 记录#返回
        井号=键.find('#')#分隔
        if 井号<=0 or 井号==len(键)-1:#畸形
            raise Exception('typert: invalid schema key "'+键+'" — expected "<package>#<name>"')#拒绝
        包名=键[:井号]#包名
        if any(候选['package']==包名 for 候选 in 自身.包们.values()):#包已登记但没有该模式
            raise Exception('typert: cannot resolve "'+键+'" — package "'+包名+'" is registered but contributes no schema named "'+键[井号+1:]+'"')#指出
        raise Exception('typert: cannot resolve "'+键+'" — package "'+包名+'" has no registered contribution')#包未登记

    def list(自身,过滤=None):#按可选过滤列出模式
        """按注册顺序枚举活模式。"""
        if 过滤 is None:#缺省
            过滤={}#空
        return [记录 for 记录 in 自身.模式们.values() if 匹配过滤(记录,过滤)]#过滤

    def getPackage(自身,包名,面='host'):#按包名与面取包记录
        """缺席为 None。"""
        return 自身.包们.get(拼包面键(包名,面))#记录

    def listPackages(自身,过滤=None):#按可选过滤列出包记录
        """按注册顺序枚举。"""
        if 过滤 is None:#缺省
            过滤={}#空
        return [记录 for 记录 in 自身.包们.values() if 匹配过滤(记录,过滤)]#过滤

    def toJSONSchema(自身,键,参数=None):#按键投影 JSON Schema
        """把一条活模式投影为 JSON Schema；若模式无 toJSONSchema 则抛。"""
        记录=自身.resolve(键)#解析
        模式=记录['schema']#模式实例
        投影=getattr(模式,'toJSONSchema',None)#投影方法
        if 投影 is None:#无投影
            raise Exception('typert: schema "'+键+'" cannot project to JSON Schema')#拒绝
        return 投影(参数) if 参数 is not None else 投影()#投影

    def 校验包(自身,贡献):#校验贡献并构造包记录
        """面必须是 host 或 client。"""
        校验段('package name',贡献['package'])#包名
        面=贡献['face']#面
        if 面!='host' and 面!='client':#非法面
            raise Exception('typert: invalid face '+repr(面)+' — expected "host" or "client"')#拒绝
        键=拼包面键(贡献['package'],面)#包-面键
        if 键 in 自身.包们:#已登记
            raise Exception('typert: package face "'+键+'" is already registered')#拒绝
        return {'package':贡献['package'],'face':面,'key':键,'model':贡献['model']}#包记录

    def 校验模式(自身,贡献):#校验贡献中的模式并构造记录
        """本批或已登记冲突则拒绝。"""
        记录们=[]#本批
        本批=set()#本批键
        for 模式 in 贡献['schemas']:#逐条
            校验段('schema name',模式['name'])#名
            键=拼模式键(贡献['package'],模式['name'])#全局键
            if 键 in 本批 or 键 in 自身.模式们:#冲突
                raise Exception('typert: schema "'+键+'" is already registered')#拒绝
            本批.add(键)#记下
            记录们.append({**模式,'package':贡献['package'],'face':贡献['face'],'key':键})#追加
        return 记录们#本批记录

# 英文别名
typertKey=拼模式键#上游名
typertPackageKey=拼包面键#上游名
typertEndpoint=拼端点#上游名
TypertRegistry=Typert注册表#上游名
