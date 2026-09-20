__all__=[
    '上下文动词','定时器动词','槽账本行字段','门面环境字段','业务视图槽名','业务视图自键',
    '拒绝门面','是否上下文返回','拒绝上下文返回','拒绝未声明读取','规范化槽登记选项',
    '登记槽并认领','主题覆盖源','覆盖主题令牌','门面可读','读服务座位','动态上下文门面','说明',
]

说明=('真实 dynamicCordisContext 需 cordis Context Proxy 与浏览器 slots/theme；'
      '本叶规则/主入口/槽认领已落地，Proxy·Reflect.apply 执行体为硬缺口。')

上下文动词=frozenset([#允许的 ctx 动词
    '副作用','监听','监听一次','提供服务','超时','间隔','节流','防抖',
])#结束

定时器动词=frozenset(['超时','间隔','节流','防抖'])#需 inject timer

槽账本行字段=('slot','priority')#账本行
门面环境字段=('pkg','ledger','claim','allocatePriority','reportFailure')#环境
业务视图槽名='tool.view.cordis'#业务视图
业务视图自键='self'#唯一可接受 key

def 是否上下文返回(值,上下文类=None):#是否 cordis Context
    """可选传入 Context 类型做 isinstance。"""
    if 上下文类 is None:#无类型
        return type(值).__name__=='Context' and hasattr(值,'纤程')#启发式
    return isinstance(值,上下文类)#精确

def 拒绝门面(环境,消息):#报告并抛
    """先报告再抛同一份错误。"""
    错误=Exception(消息)#同一份
    报告=环境.get('reportFailure') if isinstance(环境,dict) else getattr(环境,'reportFailure',None)#报告
    if callable(报告):#有
        报告(错误)#先报告
    raise 错误#再抛

def 拒绝上下文返回(值,服务名,环境,上下文类=None):#denyContext
    """服务返回 Context 则教学拒绝；否则原样。"""
    if 是否上下文返回(值,上下文类):#返回了上下文
        拒绝门面(环境,#报告并抛
            f'服务 "{服务名}" 返回了 cordis Context，动态门面不暴露它。'
            '请用自己的插件 ctx 和已声明服务操作，不要拿另一份上下文。'
        )#拒绝
    return 值#放行

def 拒绝未声明读取(环境,属性,已声明,运行时有=False):#denyRead
    """属性访问未 inject 或框架内部。"""
    if 运行时有:#运行时有这个服务但没声明
        拒绝门面(环境,#报告并抛
            f'服务 "{属性}" 未在你的插件上声明。请写在返回的插件上：'
            f"{{ inject: ['{属性}', …], apply(ctx) {{ … }} }} —— 普通 function 没有声明点，"
            '要用对象形态。提供方卸载时运行时会停放该包。'
        )#拒绝
    拒绝门面(环境,#框架内部
        f'动态 ctx 不暴露 "{属性}"。可用：ctx.on / ctx.provide、注入 timer 后的定时器助手，以及返回插件在 inject 里声明的服务'
        '（slots 与 theme 是常见 UI 座位）。框架内部按设计不外露。'
    )#拒绝

def 主题覆盖源(环境,源参数,令牌参数):#overrideTokens 参数规则
    """校验双参；返回钉死的 source 字符串（pluginId.packageId）。误把 token 图当第一参则拒。"""
    if 令牌参数 is None and isinstance(源参数,dict):#误把 token 图当第一参
        拒绝门面(环境,#教学
            'theme.overrideTokens(source, tokens) 要两个参数；source 会被换成你的包 id，'
            "所以先传任意字符串、再传令牌图：overrideTokens('mine', { '--dsw-alias-…': { light: '…', dark: '…' } })"
        )#拒绝
    包=环境.get('pkg') if isinstance(环境,dict) else getattr(环境,'pkg',None)#包
    if isinstance(包,dict):#映射
        return f"{包.get('pluginId')}.{包.get('packageId')}"#钉死
    return f'{包.pluginId}.{包.packageId}'#属性

def 门面可读(属性,已声明):#Proxy has 语义
    """门面键是否可见：get、白名单动词（定时器需已声明 timer）、或已声明服务。"""
    if 属性=='获取服务':#可选查找
        return True#可见
    if not isinstance(属性,str):#符号键
        return False#不可见
    if 属性 in 上下文动词:#白名单动词
        if 属性 in 定时器动词 and 'timer' not in 已声明:
            return False#不可见
        return True#可见
    return 属性 in 已声明#已声明服务

def 规范化槽登记选项(选项,环境,槽规格查询=None,方法名='register'):#slots.register / registerFactory 选项改写
    """分配遮蔽优先级、钉死 tool.view.cordis key。Factory 不分配优先级。账本与 claim 在登记槽并认领。"""
    if not isinstance(选项,dict):#必须对象
        拒绝门面(环境,'slots.register(options, component) needs an options object with a `name`')#教学
    出=dict(选项)#浅拷贝
    槽=出.get('name')#目标槽
    if not isinstance(槽,str) or 槽=='':#name
        拒绝门面(环境,f'slots.{方法名} options need a string `name`')#教学
    if 方法名=='registerFactory':#工厂登记不改写优先级
        出['_ledgerSlot']=f'factory:{槽}'#账本工厂键
        出['_priorityResolved']=None#工厂无遮蔽优先级
        return 出#改写后
    if 槽==业务视图槽名:#业务视图
        if 出.get('key')!=业务视图自键:#只接受 self
            拒绝门面(环境,'tool.view.cordis only accepts key "self"; the runtime binds it to this Package')#教学
        包=环境.get('pkg') if isinstance(环境,dict) else getattr(环境,'pkg',None)#包
        出['key']=f"{包.get('pluginId')}.{包.get('packageId')}" if isinstance(包,dict) else f'{包.pluginId}.{包.packageId}'#绑到本包
    规格=槽规格查询(槽) if callable(槽规格查询) else None#规格
    优先=出.get('priority')#作者写的
    if 规格 is None or (isinstance(规格,dict) and 规格.get('kind')!='chain'):#非 chain
        分配=环境.get('allocatePriority') if isinstance(环境,dict) else getattr(环境,'allocatePriority',None)#分配
        优先=分配() if callable(分配) else 优先#页本地名次
        出['priority']=优先#写入
    出['_ledgerSlot']=槽#账本槽名
    出['_priorityResolved']=优先#供登记后账本
    return 出#改写后

def 登记槽并认领(槽服务,选项,组件,环境,方法名='register'):
    """
    选项经规范化后调用真实 slots.register 或 registerFactory；仅接受成功后才 ledger.push 与 claim(component)。
    无 Proxy/Reflect.apply：以槽服务为接收者的原型 this 仍为硬缺口（Python 绑定方法可直调）。
    """
    规格查询=getattr(槽服务,'spec',None) if 槽服务 is not None else None#槽规格
    出=规范化槽登记选项(选项,环境,规格查询 if callable(规格查询) else None,方法名)#改写
    优先=出.pop('_priorityResolved',出.get('priority'))#账本优先级
    账本槽=出.pop('_ledgerSlot',出.get('name'))#账本键
    登记=getattr(槽服务,方法名,None) if 槽服务 is not None else None#真实方法
    if not callable(登记):#无座位
        拒绝门面(环境,f'slots.{方法名} is unavailable on this half (SlotRegistry hard gap)')#拒
    拆除=登记(出,组件)#以服务方法调用
    账本=环境.get('ledger') if isinstance(环境,dict) else getattr(环境,'ledger',None)#账本
    if isinstance(账本,list):#可记账
        账本.append({'slot':账本槽,'priority':优先})#登记接受之后
    认领=环境.get('claim') if isinstance(环境,dict) else getattr(环境,'claim',None)#claim
    if callable(认领):#有
        认领(组件)#注册表接受之后才认领
    return 拆除#拆除器

def 覆盖主题令牌(主题服务,环境,真实上下文,源参数,令牌参数):
    """源钉死为包 id；拆除器尽量挂到调用方 Fiber（无 effect 则只返回句柄）。"""
    源=主题覆盖源(环境,源参数,令牌参数)#钉死
    方法=getattr(主题服务,'overrideTokens',None) if 主题服务 is not None else None#真实方法
    if not callable(方法):#无
        拒绝门面(环境,'theme.overrideTokens is unavailable on this half')#拒
    拆除=方法(源,令牌参数)#调用
    if 真实上下文 is not None and callable(拆除):#Fiber 寿命
        def 挂主题拆除():
            """把主题覆盖拆除挂到调用方纤程。"""
            return 拆除#拆除器
        真实上下文.副作用(挂主题拆除,'cordis-client-runner: dynamic theme override layer')#挂清理
    return 拆除#句柄

def 读服务座位(名,服务,环境,真实上下文=None):#readService 座位分流
    """slots/theme 走专用规则入口；其余仅拒 Context 返回。无 Proxy 包装（硬缺口）。"""
    if 服务 is None or (not isinstance(服务,(dict,object)) and not callable(服务)):#标量
        return 服务#原样
    if 名=='slots':#槽座位：register / registerFactory → 规范化 → 真登记 → 账本 → claim
        def 登记(选项,组件):
            """接 claim。"""
            return 登记槽并认领(服务,选项,组件,环境,'register')#槽登记
        def 登记工厂(选项,组件):
            """工厂定义记账。"""
            return 登记槽并认领(服务,选项,组件,环境,'registerFactory')#工厂登记
        return {'service':服务,'seat':'slots','register':登记,'registerFactory':登记工厂,'normalize':规范化槽登记选项,'env':环境}#接线
    if 名=='theme':#主题座位：覆盖源钉死
        def 覆盖(源参数,令牌参数=None):
            """钉死源。"""
            return 覆盖主题令牌(服务,环境,真实上下文,源参数,令牌参数)#全路径
        return {'service':服务,'seat':'theme','overrideTokens':覆盖,'sourceOf':主题覆盖源,'env':环境,'ctx':真实上下文}#接线
    return {'service':服务,'seat':'generic','env':环境,'name':名}#通用（方法转发需 Proxy/Reflect.apply 硬缺口）

def 动态上下文门面(真实上下文,环境):#dynamicCordisContext 主入口（无 Proxy）
    """
    按门面可读键与 get/动词/已声明服务分流；slots.register 接认领；theme 源钉死。
    不构造 Proxy、不绑 Reflect.apply（硬缺口）。返回可查询/可调用的门面描述。
    """
    依赖=getattr(getattr(真实上下文,'纤程',None),'inject',None) or {}
    已声明=set(依赖.keys() if isinstance(依赖,dict) else [])
    def 获取(名,须声明=False):#ctx.get / 属性
        """读服务；未声明属性访问拒。"""
        if 须声明 and 名 not in 已声明:#属性门
            运行时有=真实上下文.获取服务(名) is not None#运行时
            拒绝未声明读取(环境,名,已声明,运行时有)#抛
        值=真实上下文.获取服务(名)#取
        拒绝上下文返回(值,名,环境)#拒 Context
        if 值 is None or (not isinstance(值,(dict,list)) and not callable(值) and not hasattr(值,'__dict__')):#标量
            return 值#原样
        return 读服务座位(名,值,环境,真实上下文)#座位
    def 调动词(动词,*位置参数):#白名单动词
        """定时器须已声明 timer；真实方法转发若上下文有该名。"""
        if 动词 in 定时器动词 and 'timer' not in 已声明:
            拒绝未声明读取(环境,'timer',已声明,False)#抛
        方法=getattr(真实上下文,动词,None)#真实
        if not callable(方法):#无
            拒绝未声明读取(环境,动词,已声明,False)#抛
        return 方法(*位置参数)#绑在真实 ctx（无 Reflect 硬缺口：普通调用）
    def 取属性(属性):
        """get / 动词 / 已声明服务。"""
        if 属性=='获取服务':#可选查找
            def 可选查找(名):
                """不要求声明的查找。"""
                return 获取(名,False)#查找
            return 可选查找#查找
        if not isinstance(属性,str):#符号键
            return None#不暴露
        if 属性 in 上下文动词:#白名单
            def 转发动词(*位置参数,动词=属性):
                """惰性转发白名单动词。"""
                return 调动词(动词,*位置参数)#转发
            return 转发动词#惰性转发
        return 获取(属性,True)#已声明属性
    def 写属性(属性,_值=None):
        """只读。"""
        拒绝门面(环境,f'dynamic ctx is read-only; cannot assign "{属性}"')#拒
    def 可选查找入口(名):
        """不要求声明的查找。"""
        return 获取(名,False)#查找
    def 已声明入口(名):
        """已声明属性读取。"""
        return 获取(名,True)#已声明
    def 是否可读(属性):
        """Proxy has 语义。"""
        return 门面可读(属性,已声明)#可见
    return {#门面描述（非 Proxy；装配/求值接线用）
        'get':可选查找入口,#可选查找
        'readDeclared':已声明入口,#已声明属性
        'getattr':取属性,#Proxy get 等价
        'setattr':写属性,#Proxy set 等价
        'hasattr':是否可读,#Proxy has
        'verbs':上下文动词,#白名单
        'timerVerbs':定时器动词,#定时器
        'declared':已声明,#inject
        'callableVerb':调动词,#动词入口
        'readable':是否可读,#has 语义
        'hardGap':'Proxy/Reflect.apply/slots.register this — not implemented',#硬缺口
    }#结束
