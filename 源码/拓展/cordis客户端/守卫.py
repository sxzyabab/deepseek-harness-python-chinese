"""动态包上下文门面：生命周期安全动词白名单与槽/主题座位规则。

对齐上游 `cordis-client-runner/src/client/guard.ts`。公开面仅中文名。
硬缺口（保留不通过，勿假实现）：真实 Proxy 门面、`Reflect.apply` 绑 this、
SlotRegistry.prototype.register 接收者、theme 层 `ctx.effect` 拆除依赖真实 Fiber、React 组件认领键。
本模块落盘白名单、教学拒绝、槽/主题规则（含 register 后 claim）、主入口分流。
"""

__all__=[#仅中文公开名（对齐 guard.ts 可迁规则面；Proxy 执行体硬缺口）
    '上下文动词','定时器动词','槽账本行字段','守卫环境字段','业务视图槽名','业务视图自键',
    '拒绝守卫','是否上下文返回','拒绝上下文返回','拒绝未声明读取','规范化槽登记选项',
    '守卫槽登记','主题覆盖源','守卫主题覆盖','门面可读','读服务座位','动态上下文门面','说明',
]#公开面结束

说明=('真实 dynamicCordisContext 需 cordis Context Proxy 与浏览器 slots/theme；'
      '本叶规则/主入口/槽 claim 已对齐，Proxy·Reflect.apply 执行体为硬缺口。')#说明

上下文动词=frozenset([#允许的 ctx 动词
    'effect','on','once','provide','timeout','interval','setTimeout','setInterval','throttle','debounce',
])#结束

定时器动词=frozenset(['timeout','interval','setTimeout','setInterval','throttle','debounce'])#需 inject timer

槽账本行字段=('slot','priority')#账本行
守卫环境字段=('pkg','ledger','claim','allocatePriority','reportFailure')#环境
业务视图槽名='tool.view.cordis'#业务视图
业务视图自键='self'#唯一可接受 key

def 是否上下文返回(值,上下文类=None):#是否 cordis Context
    """可选传入 Context 类型做 isinstance。"""
    if 上下文类 is None:#无类型
        return type(值).__name__=='Context' and hasattr(值,'fiber')#启发式
    return isinstance(值,上下文类)#精确

def 拒绝守卫(环境,消息):#报告并抛
    """对齐 rejectGuard。"""
    错误=Exception(消息)#同一份
    报告=环境.get('reportFailure') if isinstance(环境,dict) else getattr(环境,'reportFailure',None)#报告
    if callable(报告):#有
        报告(错误)#先报告
    raise 错误#再抛

def 拒绝上下文返回(值,服务名,环境,上下文类=None):#denyContext
    """服务返回 Context 则教学拒绝；否则原样。"""
    if 是否上下文返回(值,上下文类):#返回了上下文
        拒绝守卫(环境,#报告并抛
            f'service "{服务名}" returned a cordis Context, which the dynamic facade does not expose. '
            'Operate through your own plugin ctx and the services you declared — never another context.'
        )#拒绝
    return 值#放行

def 拒绝未声明读取(环境,属性,已声明,运行时有=False):#denyRead
    """属性访问未 inject 或框架内部。"""
    if 运行时有:#运行时有这个服务但没声明
        拒绝守卫(环境,#报告并抛
            f'service "{属性}" is not declared by your plugin. Declare it on the plugin you return: '
            f"{{ inject: ['{属性}', …], apply(ctx) {{ … }} }} — a plain `function` has no declaration site, "
            'so use the object form. The runtime then parks the package if the provider unloads.'
        )#拒绝
    拒绝守卫(环境,#框架内部
        f'dynamic ctx does not expose "{属性}". Available: ctx.on / ctx.provide / timer helpers after injecting timer, and any service your '
        'returned plugin declared in inject (slots and theme are the usual UI seats). Framework internals are withheld '
        'by design.'
    )#拒绝

def 主题覆盖源(环境,源参数,令牌参数):#overrideTokens 参数规则
    """校验双参；返回钉死的 source 字符串（pluginId.packageId）。误把 token 图当第一参则拒。"""
    if 令牌参数 is None and isinstance(源参数,dict):#误把 token 图当第一参
        拒绝守卫(环境,#教学
            'theme.overrideTokens(source, tokens) takes two arguments; source is replaced with your package id, '
            "so pass any string first and the token map second: overrideTokens('mine', { '--dsw-alias-…': { light: '…', dark: '…' } })"
        )#拒绝
    包=环境.get('pkg') if isinstance(环境,dict) else getattr(环境,'pkg',None)#包
    if isinstance(包,dict):#映射
        return f"{包.get('pluginId')}.{包.get('packageId')}"#钉死
    return f'{包.pluginId}.{包.packageId}'#属性

def 门面可读(属性,已声明):#Proxy has 语义
    """门面键是否可见：get、白名单动词（定时器需已声明 timer）、或已声明服务。"""
    if 属性=='get':#可选查找
        return True#可见
    if not isinstance(属性,str):#符号键
        return False#不可见
    if 属性 in 上下文动词:#白名单动词
        if 属性 in 定时器动词 and 'timer' not in 已声明:#定时器未注入
            return False#不可见
        return True#可见
    return 属性 in 已声明#已声明服务

def 规范化槽登记选项(选项,环境,槽规格查询=None):#slots.register 选项改写（不含账本/claim）
    """分配遮蔽优先级、钉死 tool.view.cordis key。返回改写后的选项；账本与 claim 在守卫槽登记。"""
    if not isinstance(选项,dict):#必须对象
        拒绝守卫(环境,'slots.register(options, component) needs an options object with a `name`')#教学
    出=dict(选项)#浅拷贝
    槽=出.get('name')#目标槽
    if not isinstance(槽,str) or 槽=='':#name
        拒绝守卫(环境,'slots.register options need a string `name` (the target slot key)')#教学
    if 槽==业务视图槽名:#业务视图
        if 出.get('key')!=业务视图自键:#只接受 self
            拒绝守卫(环境,'tool.view.cordis only accepts key "self"; the runtime binds it to this Package')#教学
        包=环境.get('pkg') if isinstance(环境,dict) else getattr(环境,'pkg',None)#包
        出['key']=f"{包.get('pluginId')}.{包.get('packageId')}" if isinstance(包,dict) else f'{包.pluginId}.{包.packageId}'#绑到本包
    规格=槽规格查询(槽) if callable(槽规格查询) else None#规格
    优先=出.get('priority')#作者写的
    if 规格 is None or (isinstance(规格,dict) and 规格.get('kind')!='chain'):#非 chain
        分配=环境.get('allocatePriority') if isinstance(环境,dict) else getattr(环境,'allocatePriority',None)#分配
        优先=分配() if callable(分配) else 优先#页本地名次
        出['priority']=优先#写入
    出['_priorityResolved']=优先#供登记后账本（不进真实 register 选项）
    return 出#改写后

def 守卫槽登记(槽服务,选项,组件,环境):#对齐 guardedSlots.register：先 register，再账本，再 claim
    """
    选项经规范化后调用真实 slots.register；仅接受成功后才 ledger.push 与 claim(component)。
    无 Proxy/Reflect.apply：以槽服务为接收者的原型 this 仍为硬缺口（Python 绑定方法可直调）。
    """
    规格查询=getattr(槽服务,'spec',None) if 槽服务 is not None else None#槽规格
    出=规范化槽登记选项(选项,环境,规格查询 if callable(规格查询) else None)#改写
    优先=出.pop('_priorityResolved',出.get('priority'))#账本优先级
    槽=出.get('name')#槽名
    登记=getattr(槽服务,'register',None) if 槽服务 is not None else None#真实 register
    if not callable(登记):#无座位
        # 硬缺口：无浏览器 SlotRegistry 时不冒充登记成功，也不 claim（避免污染所有者索引）
        拒绝守卫(环境,'slots.register is unavailable on this half (SlotRegistry hard gap)')#拒
    拆除=登记(出,组件)#以服务方法调用（对齐 register.call(target,…) 意图；无 Reflect）
    账本=环境.get('ledger') if isinstance(环境,dict) else getattr(环境,'ledger',None)#账本
    if isinstance(账本,list):#可记账
        账本.append({'slot':槽,'priority':优先})#登记接受之后
    认领=环境.get('claim') if isinstance(环境,dict) else getattr(环境,'claim',None)#claim
    if callable(认领):#有
        认领(组件)#注册表接受之后才认领
    return 拆除#拆除器

def 守卫主题覆盖(主题服务,环境,真实上下文,源参数,令牌参数):#对齐 guardedTheme.overrideTokens
    """源钉死为包 id；拆除器尽量挂到调用方 Fiber（无 effect 则只返回句柄）。"""
    源=主题覆盖源(环境,源参数,令牌参数)#钉死
    方法=getattr(主题服务,'overrideTokens',None) if 主题服务 is not None else None#真实方法
    if not callable(方法):#无
        拒绝守卫(环境,'theme.overrideTokens is unavailable on this half')#拒
    拆除=方法(源,令牌参数)#调用
    if 真实上下文 is not None and hasattr(真实上下文,'effect') and callable(拆除):#Fiber 寿命
        真实上下文.effect(lambda:拆除,'cordis-client-runner: dynamic theme override layer')#挂清理
    return 拆除#句柄

def 读服务座位(名,服务,环境,真实上下文=None):#readService 座位分流
    """slots/theme 走专用规则入口；其余仅拒 Context 返回。无 Proxy 包装（硬缺口）。"""
    if 服务 is None or (not isinstance(服务,(dict,object)) and not callable(服务)):#标量
        return 服务#原样
    if 名=='slots':#槽座位：register → 规范化 → 真登记 → 账本 → claim
        def 登记(选项,组件):#对齐 Proxy register
            """接 claim。"""
            return 守卫槽登记(服务,选项,组件,环境)#全路径
        return {'service':服务,'seat':'slots','register':登记,'normalize':规范化槽登记选项,'env':环境}#接线
    if 名=='theme':#主题座位：覆盖源钉死
        def 覆盖(源参数,令牌参数=None):#对齐 Proxy overrideTokens
            """钉死源。"""
            return 守卫主题覆盖(服务,环境,真实上下文,源参数,令牌参数)#全路径
        return {'service':服务,'seat':'theme','overrideTokens':覆盖,'sourceOf':主题覆盖源,'env':环境,'ctx':真实上下文}#接线
    return {'service':服务,'seat':'generic','env':环境,'name':名}#通用（方法转发需 Proxy/Reflect.apply 硬缺口）

def 动态上下文门面(真实上下文,环境):#dynamicCordisContext 主入口（无 Proxy）
    """
    对齐门面可读键与 get/动词/已声明服务分流；slots.register 接 claim；theme 源钉死。
    不构造 Proxy、不绑 Reflect.apply（硬缺口）。返回可查询/可调用的门面描述。
    """
    注入=getattr(getattr(真实上下文,'fiber',None),'inject',None) or {}#inject
    已声明=set(注入.keys() if isinstance(注入,dict) else [])#已声明
    def 获取(名,须声明=False):#ctx.get / 属性
        """读服务；未声明属性访问拒。"""
        if 须声明 and 名 not in 已声明:#属性门
            运行时有=真实上下文.get(名) is not None if hasattr(真实上下文,'get') else False#运行时
            拒绝未声明读取(环境,名,已声明,运行时有)#抛
        值=真实上下文.get(名) if hasattr(真实上下文,'get') else None#取
        拒绝上下文返回(值,名,环境)#拒 Context
        if 值 is None or (not isinstance(值,(dict,list)) and not callable(值) and not hasattr(值,'__dict__')):#标量
            return 值#原样
        return 读服务座位(名,值,环境,真实上下文)#座位
    def 调动词(动词,*位置参数):#白名单动词
        """定时器须已声明 timer；真实方法转发若上下文有该名。"""
        if 动词 in 定时器动词 and 'timer' not in 已声明:#未注入
            拒绝未声明读取(环境,'timer',已声明,False)#抛
        方法=getattr(真实上下文,动词,None)#真实
        if not callable(方法):#无
            拒绝未声明读取(环境,动词,已声明,False)#抛
        return 方法(*位置参数)#绑在真实 ctx（无 Reflect 硬缺口：普通调用）
    def 取属性(属性):#对齐 Proxy get
        """get / 动词 / 已声明服务。"""
        if 属性=='get':#可选查找
            return lambda 名:获取(名,False)#查找
        if not isinstance(属性,str):#符号键
            return None#不暴露
        if 属性 in 上下文动词:#白名单
            return lambda *位置参数:调动词(属性,*位置参数)#惰性转发
        return 获取(属性,True)#已声明属性
    def 写属性(属性,_值=None):#对齐 Proxy set
        """只读。"""
        拒绝守卫(环境,f'dynamic ctx is read-only; cannot assign "{属性}"')#拒
    return {#门面描述（非 Proxy；装配/求值接线用）
        'get':lambda 名:获取(名,False),#可选查找
        'readDeclared':lambda 名:获取(名,True),#已声明属性
        'getattr':取属性,#Proxy get 等价
        'setattr':写属性,#Proxy set 等价
        'hasattr':lambda 属性:门面可读(属性,已声明),#Proxy has
        'verbs':上下文动词,#白名单
        'timerVerbs':定时器动词,#定时器
        'declared':已声明,#inject
        'callableVerb':调动词,#动词入口
        'readable':lambda 属性:门面可读(属性,已声明),#has 语义
        'hardGap':'Proxy/Reflect.apply/slots.register this — not implemented',#硬缺口
    }#结束
