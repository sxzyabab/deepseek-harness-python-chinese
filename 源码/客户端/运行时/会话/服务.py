"""SessionRuntime：根会话服务 — 列表快照存储、Agent 作用域树、稳定装配缓存、面包屑路由投影。

对齐上游 `runtime/src/client/sessions/service.ts`。公开面仅中文名；协议键保持上游英文。

作用域生命周期由舞台驱动：作用域在首次解析时惰性铸造；
事件窗口与推迟拆除键在 STAGED 会话上，精确跟随 list.current。
会话离开列表立刻拆掉其作用域，除非它是 staged 的那个，其作用域冻结存活直到舞台挪走。

依赖未迁：SessionRemotes（仅构造入参类型，上游 remotes.ts）；
`host.apiproxy.接口.会话搜索结果上限`（上游 SESSION_SEARCH_RESULT_LIMIT，本叶直接导入）；
`dsh-client-ui-slots`（HostObservable / SessionMaybeProvideInfo / SessionProvideInfo，以鸭式映射表达）；
`dsh-session-projection/types`（SessionProjectionMap，投影值以映射表达）；
Cordis Context / Fiber（以鸭式根上下文与光纤表达）。
对话运行时邻叶键用「事件」「视图」（对齐会话.py；上游 ConversationRuntime 为 events/views）。
"""
import asyncio#注册表重建微任务
import math#分叉锚点向下取整
import re#分叉标题括号编号
from ..约定.存储 import 创建快照存储#快照存储工厂
from ..客户端.智能体.作用域 import 铸造作用域,作用域身份#作用域铸造与标签读取
from .管理器 import 会话管理器#对象层管理器
from .提供 import 会话提供通道#provide 通道

__all__=[#仅中文公开名
    '会话摘要',
    '会话列表状态',
    '会话创建错误',
    '会话分叉错误',
    '会话装配',
    '会话提供贡献',
    '会话提供描述符',
    '工作区标题于',
    '作用域身份',
    '会话运行时',
]#公开面结束

# 作用域原语住在客户端/智能体/作用域.py；在此再导出，让现有消费方保持导入点。
scopeOf=作用域身份#上游再导出名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 火忘(协程或结果):#fire-and-forget
    """有环则挂 Task；无环则交给宿主稍后驱动。"""
    if asyncio.iscoroutine(协程或结果):#协程
        try:#有环
            asyncio.get_running_loop().create_task(协程或结果)#挂任务
        except RuntimeError:#无环
            pass#宿主稍后驱动
        return#结束
    if callable(getattr(协程或结果,'__await__',None)):#awaitable
        try:#有环
            asyncio.get_running_loop().create_task(协程或结果)#挂任务
        except RuntimeError:#无环
            pass#宿主稍后驱动

def 工作区标题于(工作目录):#cwd → 基名
    """会话 cwd 的工作区展示标题：路径最后一个非空段。

    两种分隔符都接受；忽略尾部分隔符；只有分隔符的路径则为 ''。
    @param 工作目录 - 工作区目录路径。
    @returns 基名标题；没有非空段时为 ''。
    """
    去尾=re.sub(r'[/\\]+$','',工作目录)#去掉尾部分隔
    段们=re.split(r'[/\\]',去尾)#按分隔切开
    return 段们[-1] if 段们 else ''#最后一段；空则 ''

workspaceTitleOf=工作区标题于#上游名

def 展示标题于(标题,工作目录,标识):#行展示标题
    """展示标题投影：持久标题、项目目录基名，然后才是原始 id。"""
    if 标题 is not None:#有持久标题优先
        return 标题#持久标题
    if 工作目录 is not None and 工作目录!='':#有工作目录
        基名=工作区标题于(工作目录)#取基名
        if 基名!='':#非空基名
            return 基名#基名
    return 标识#最后用会话 id

def 递增分叉标题(标题):#fork 标题加一
    """递增尾部的 fork 编号，同时保留半角或全角括号；未编号的标题从 ` (1)` 起。

    @param 标题 - 源会话的持久标题。
    @returns 赋给 fork 子会话的标题。
    """
    半角=re.match(r'^(.*?)\((\d+)\)$',标题,flags=re.UNICODE)#半角括号数字
    if 半角 is not None and 半角.group(1) is not None and 半角.group(2) is not None:#匹配到半角
        return 半角.group(1)+'('+str(int(半角.group(2))+1)+')'#数字加一
    全角=re.match(r'^(.*?)（(\d+)）$',标题,flags=re.UNICODE)#全角括号数字
    if 全角 is not None and 全角.group(1) is not None and 全角.group(2) is not None:#匹配到全角
        return 全角.group(1)+'（'+str(int(全角.group(2))+1)+'）'#数字加一
    return 标题+' (1)'#原先无编号

class 会话摘要:#列表行（协议字段文档）
    """从宿主列表 RPC 加上在线流增量投影出的会话列表行。

    协议键：id / title / displayTitle / cwd / agentPreset / parentId / origin /
    running / pendingInteraction / completed / blank / updatedAt / projectionValues。
    """

class 会话列表状态:#列表快照（协议字段文档）
    """会话列表存储形态；current 骑在同一份快照上。

    协议键：ids / byId / current / phase / subagentsByParent / jobsBySession / currentAddress。
    """

class 会话装配:#作用域组装句柄文档
    """给 SessionProvider/inject 工厂用的会话组装句柄（每个会话身份稳定）。

    协议键：sessionId / session / ctx。
    """

class 会话提供贡献:#provide 贡献文档
    """一个插件按会话贡献的标准道具。

    协议键：hooks / props。
    """

class 会话提供描述符:#provide 描述符文档
    """一份标准套件贡献的静态声明加上按会话解析器。

    协议键：hooks / props / resolve。
    """

class 会话创建错误(Exception):#创建失败
    """结构化的会话创建失败。"""

    def __init__(自身,rpc错误,请求会话标识=None):#记下 RPC 错误与请求 id
        """@param rpc错误 - 宿主业务或折叠后的传输错误。
        @param 请求会话标识 - 调用方预分配的 id，供稍后流/列表对账。
        """
        码=取字段(rpc错误,'code','')#码
        消息=取字段(rpc错误,'message','')#消息
        super().__init__('session create failed: '+str(码)+': '+str(消息))#拼消息
        自身.rpcError=rpc错误#宿主错误
        自身.requestedSessionId=请求会话标识#预分配 id
        自身.name='SessionCreateError'#固定错误名

class 会话分叉错误(Exception):#fork 失败
    """结构化的会话 fork 失败。"""

    def __init__(自身,rpc错误,源会话标识):#记下 RPC 错误与源 id
        """@param rpc错误 - 宿主业务或折叠后的传输错误。
        @param 源会话标识 - fork 切出的源会话。
        """
        码=取字段(rpc错误,'code','')#码
        消息=取字段(rpc错误,'message','')#消息
        super().__init__('session fork failed: '+str(码)+': '+str(消息))#拼消息
        自身.rpcError=rpc错误#宿主错误
        自身.sourceSessionId=源会话标识#源会话
        自身.name='SessionForkError'#固定错误名

class 会话运行时:#根会话运行时
    """根会话服务：列表存储、当前选择、对象层管理器、作用域树、绑定，以及面包屑路由。"""

    def __init__(自身,根上下文,接口,远程,对话运行时=None):#组装列表存储、管理器、provide 通道
        """@param 根上下文 - 客户端根上下文（作用域光纤挂在它下面）。
        @param 接口 - 与每个 Session 共用的线客户端。
        @param 远程 - 与每个 Session 共用的生成 Remote 命名空间（依赖未迁类型 SessionRemotes）。
        @param 对话运行时 - 同一趟 apply 拥有的注册表实例，可选。
        """
        自身._根上下文=根上下文#根上下文
        自身.searchResultLimit=会话搜索结果上限#搜索结果上限（协议属性）
        自身.搜索结果上限=会话搜索结果上限#中文别名
        自身._选择=创建快照存储(#持久选择存储
            {},#默认空选择
            {'persist':{'name':'dsh.sessions.current'}},#本地持久名
        )#结束选择
        已恢复=自身._选择.取快照()#读出上次选择
        对话事件=根上下文.get('conversationEvents') if hasattr(根上下文,'get') else None#可选事件注册表
        对话视图=根上下文.get('conversationViews') if hasattr(根上下文,'get') else None#可选视图注册表
        if 对话运行时 is not None:#优先用传入的
            对话=对话运行时#传入运行时
        elif 对话事件 is None or 对话视图 is None:#缺任一侧
            对话=None#没有会话运行时
        else:#从上下文拼（邻叶会话.py 读「事件」「视图」）
            对话={'事件':对话事件,'视图':对话视图}#拼成运行时
        自身._管理器=会话管理器(#对象层
            接口,#线客户端
            远程,#Remote
            取字段(已恢复,'sessionId'),#恢复的当前会话
            取字段(已恢复,'subagentAddress'),#恢复的子智能体地址
            对话,#会话注册表
        )#结束会话管理器
        自身.list=创建快照存储({#列表存储初始空（协议属性 list）
            'ids':[],#空列表
            'byId':{},#空行表
            'current':None,#无选中
            'phase':'pending',#待到达
            'subagentsByParent':{},#空名册
            'jobsBySession':{},#空任务
            'currentAddress':None,#无地址
        })#结束 list
        自身._作用域们={}#已铸造作用域 sessionId → 记录
        自身._监视中=None#当前舞台会话
        自身._推迟拆除=set()#推迟拆除集
        class _通道宿主:#provide 通道宿主钩
            """拥有方侧的包存储与当前选择解析。"""

            def 重建包(宿主自身):#名册变则重建已有作用域的包
                """按新名册重新物化每一个已经物化过的包。"""
                for 记录 in 自身._作用域们.values():#每个作用域
                    记录['provideInfo']=自身._提供通道.物化信息(记录['binding'])#重新物化

            def 解析当前(宿主自身):#当前会话的可空包
                """解析当前选择的包。"""
                return 自身._可空提供信息(取字段(自身.list.取快照(),'current'))#当前会话的可空包
        自身._提供通道=会话提供通道(_通道宿主())#provide 通道
        自身.currentProvideInfo=自身._提供通道.当前提供信息#对外可观察（协议属性）
        自身.当前提供信息=自身._提供通道.当前提供信息#中文别名
        自身._管理器.订阅(lambda:自身._投影列表())#管理器变则投影列表
        def _列表变更():#列表变则跟舞台并发布 provide
            """上台/开窗口，并发布当前 provide 包。"""
            自身._跟随当前()#上台/开窗口
            自身._提供通道.发布当前()#发布当前包
        自身.list.订阅(_列表变更)#列表变更订阅
        自身._注册表重建已排队=False#注册表重建是否已排队
        if 对话 is not None and hasattr(根上下文,'effect'):#有会话注册表才订
            def 调度注册表重建():#微任务合并重建
                """合并多次名册变更为一次重建。"""
                if 自身._注册表重建已排队:#已排队则跳过
                    return#跳过
                自身._注册表重建已排队=True#标记已排队
                def 跑():#下一微任务
                    """清标记并重建。"""
                    自身._注册表重建已排队=False#清标记
                    自身._管理器.重建会话注册表()#重建会话注册表
                try:#有环则 call_soon
                    asyncio.get_running_loop().call_soon(跑)#下一事件环嘀嗒
                except RuntimeError:#无环
                    跑()#同步跑，避免丢重建
            def 挂订阅():#订阅事件/视图变更
                """登记两边名册订阅；返回拆除。"""
                拆除事件=取字段(对话,'事件').subscribe(调度注册表重建)#事件名册变
                拆除视图=取字段(对话,'视图').subscribe(调度注册表重建)#视图名册变
                def 拆除():#拆除订阅
                    """取消两边订阅。"""
                    拆除事件()#取消事件
                    拆除视图()#取消视图
                return 拆除#拆除器
            根上下文.effect(挂订阅,'sessions: conversation registry rebuild')#effect 名
        提供=getattr(getattr(根上下文,'reflect',None),'provide',None)#reflect.provide
        if callable(提供):#有注入面
            提供('sessions',自身,None)#注入 ctx.sessions
        elif hasattr(根上下文,'provide') and callable(根上下文.provide):#退化 provide
            根上下文.provide('sessions',自身)#注入

    def 提供(自身,描述符):#登记 provide
        """登记一个按会话的标准道具提供方。

        @param 描述符 - 静态成员名册加上按会话解析器。
        @returns 去掉该提供方的 disposer。
        """
        return 自身._提供通道.提供(描述符)#交给通道

    provide=提供#协议名

    def 打开(自身,标识):#打开会话
        """把一个已列出或保留的名册寻址会话选为当前。

        @param 标识 - 已列出或已寻址的会话 id。
        """
        自身._管理器.选中(标识)#交给管理器选择

    open=打开#协议名

    def 打开子智能体(自身,地址):#打开子智能体
        """经直接父地址打开一个健康的名册子项。

        @param 地址 - 名册导出的父子 id。
        """
        自身._管理器.选中子智能体(地址)#交给管理器

    openSubagent=打开子智能体#协议名

    def 子智能体地址(自身,标识):#查子智能体地址
        """解析一个已经发现的直接父地址，但不打开它。

        @param 标识 - 可能的已寻址子 id。
        @returns 保留的地址，若有。
        """
        return 自身._管理器.子智能体地址(标识)#交给管理器

    subagentAddress=子智能体地址#协议名

    def 设子智能体名册开闭(自身,父会话标识,开着):#名册菜单开关
        """告知运行时某个名册菜单是否在消费成员更新。

        @param 父会话标识 - 所选父。
        @param 开着 - 菜单状态。
        """
        自身._管理器.设子智能体名册开闭(父会话标识,开着)#交给管理器

    setSubagentCatalogOpen=设子智能体名册开闭#协议名

    def 刷新子智能体(自身,父会话标识):#刷新名册
        """刷新一份直接子名册。

        @param 父会话标识 - 名册所有者。
        @returns 刷新完成的 awaitable。
        """
        return 自身._管理器.刷新子智能体(父会话标识)#交给管理器

    refreshSubagents=刷新子智能体#协议名

    def 记下智能体预设(自身,会话标识,智能体预设):#记下会话实际跑的预设
        """记录宿主确认的组合切换。"""
        自身._管理器.记下智能体预设(会话标识,智能体预设)#交给管理器

    noteAgentPreset=记下智能体预设#协议名

    def 清空(自身):#清空选择
        """清掉当前选择，让布局展示无会话空状态。

        也擦掉持久选择；staged 作用域按掩盖缺口约定保住冻结视图，直到下一次打开挪舞台。
        """
        自身._管理器.清空选择()#交给管理器

    clear=清空#协议名

    def 刷新(自身):#刷新列表
        """刷新真实会话基线，复用飞行中的拉取。

        @returns 当前或新启动的基线拉取完成。
        """
        return 自身._管理器.刷新列表()#交给管理器

    refresh=刷新#协议名

    def 搜索(自身,查询,取消信号=None):#搜索消息
        """搜索宿主可见的消息内容索引。结果留在请求本地。

        @param 查询 - 非空白字面短语。
        @param 取消信号 - 被替代搜索的取消。
        @returns 有界结果，或业务/传输错误。
        """
        return 自身._管理器.搜索(查询,取消信号)#交给管理器

    search=搜索#协议名

    def 处理复用信封(自身,信封):#mux 帧
        """把一条 mux 流信封路由进会话对象层。"""
        自身._管理器.处理复用信封(信封)#交给管理器

    handleMuxEnvelope=处理复用信封#协议名

    def 处理宿主信封(自身,信封):#host 帧
        """把一条宿主流信封路由进会话对象层。"""
        自身._管理器.处理宿主信封(信封)#交给管理器

    handleHostEnvelope=处理宿主信封#协议名

    def 处理已连接(自身):#世代握手完成
        """连接后重建会话基线与每个已打开窗口。"""
        自身._管理器.处理已连接()#交给管理器 resync

    handleConnected=处理已连接#协议名

    def 处理已断开(自身):#世代死亡
        """一个连接世代一死就丢掉世代作用域的在线交互状态。"""
        自身._管理器.处理已断开()#交给管理器

    handleDisconnected=处理已断开#协议名

    async def 创建(自身,选项=None):#创建会话
        """在宿主上创建会话。

        兑现时新建会话已在列表存储里，且 装配() 能解析它。
        @param 选项 - 目标工作区或目录，以及可选的预分配 id。
        @returns 新会话 id。
        @raises 会话创建错误 带着请求 id。
        """
        if 选项 is None:#默认空
            选项={}#空选项
        结果=await 自身._管理器.创建(选项)#宿主创建
        if not 取字段(结果,'ok'):#失败
            raise 会话创建错误(取字段(结果,'error'),取字段(选项,'sessionId'))#结构化抛出
        自身._投影列表()#同步投影，保证立刻可寻址
        return 取字段(取字段(结果,'value'),'sessionId')#新 id

    create=创建#协议名

    async def 分叉(自身,选项):#从源 fork
        """从源会话一个已完成回合前缀 fork。

        @param 选项 - sessionId、可选 atSeq、可选 increaseTitle。
        @returns 子会话 id。
        @raises 会话分叉错误 带着源 id。
        @raises Exception 当请求的子标题重命名在创建后失败。
        """
        要递增=bool(取字段(选项,'increaseTitle'))#是否递增标题
        源标识=取字段(选项,'sessionId')#源会话
        if 要递增:#要递增才读源标题
            源行=取字段(自身.list.取快照(),'byId',{}).get(源标识)#源列表行
            源标题=取字段(源行,'title')#源持久标题
        else:#不递增
            源标题=None#不读
        分叉参数={'sessionId':源标识}#宿主 fork 参数
        锚点=取字段(选项,'atSeq')#可选切点 seq
        if 锚点 is not None:#有锚点则向下取整
            分叉参数['atSeq']=math.floor(锚点)#落到真实事件 seq
        结果=await 自身._管理器.分叉(分叉参数)#宿主 fork
        if not 取字段(结果,'ok'):#失败
            raise 会话分叉错误(取字段(结果,'error'),源标识)#结构化抛出
        自身._投影列表()#同步投影
        子标识=取字段(取字段(结果,'value'),'sessionId')#子 id
        if 源标题 is not None:#需要递增标题
            子装配=自身.装配(子标识)#取子装配
            子面=取字段(子装配,'session') if 子装配 is not None else None#子对外面
            if 子面 is None:#投影后仍不可寻址
                raise Exception('fork child "'+str(子标识)+'" is not locally addressable')#不可寻址
            已改=await 子面.重命名(递增分叉标题(源标题))#重命名
            if not 取字段(已改,'ok'):#重命名失败
                错=取字段(已改,'error')#错误
                raise Exception('fork child rename failed: '+str(取字段(错,'code'))+': '+str(取字段(错,'message')))#重命名失败
        return 子标识#子 id

    fork=分叉#协议名

    def 作用域(自身,标识):#取作用域上下文
        """解析一个 Agent 作用域上下文视图（用完即弃）。

        @param 标识 - 会话 id（智能体身份 — 1:1 同一轴）。
        @returns 作用域 ctx；既未列出也尚未有作用域的会话则为 None。
        """
        记录=自身._解析(标识)#惰性铸造后取出
        return 取字段(记录,'ctx') if 记录 is not None else None#作用域上下文

    scope=作用域#协议名

    def 作用域于(自身,上下文):#读作用域标签
        """从一个上下文读出 Agent 作用域标签。

        @param 上下文 - 任意客户端上下文。
        @returns 会话 id；根上下文则为 None。
        """
        return 作用域身份(上下文)#同一模块实例的标签键

    scopeOf=作用域于#协议名

    def 会话于(自身,上下文):#ctx → 会话面
        """解析 Agent 作用域上下文背后的业务 Session。

        @param 上下文 - 一个 Agent 作用域上下文。
        @returns 会话面；ctx 无标签或其作用域已被修剪则为 None。
        """
        标识=作用域身份(上下文)#读标签
        if 标识 is None:#根上下文
            return None#无会话
        记录=自身._作用域们.get(标识)#已铸造才有
        return 取字段(取字段(记录,'binding'),'session') if 记录 is not None else None#对外面

    sessionOf=会话于#协议名

    def 装配(自身,标识):#取绑定
        """解析稳定的会话绑定（作用域寻址的组装源）。纯解析 — 无 staging、无窗口副作用。

        @param 标识 - 会话 id。
        @returns 绑定；既未列出也尚未有作用域的会话则为 None。
        """
        记录=自身._解析(标识)#惰性铸造
        return 取字段(记录,'binding') if 记录 is not None else None#装配句柄

    binding=装配#协议名

    def _提供信息(自身,标识):#确定会话的包
        """解析一个会话的渲染层标准道具包。纯解析 — 渲染安全。"""
        记录=自身._解析(标识)#惰性铸造后取出
        return 取字段(记录,'provideInfo') if 记录 is not None else None#标准道具包

    def _可空提供信息(自身,标识):#可空当前包
        """解析当前会话可选的标准套件。未知或缺席的 id 返回静态无会话投影。"""
        if 标识 is None:#无选中
            return 自身._提供通道.可空信息#静态投影
        信息=自身._提供信息(标识)#确定包
        return 信息 if 信息 is not None else 自身._提供通道.可空信息#无会话用静态投影

    def _跟随当前(自身):#跟随 current 上台
        """把舞台挪到列表的当前会话：扫推迟拆除，并拉新占用者的历史窗口。"""
        快照=自身.list.取快照()#当前列表
        当前=取字段(快照,'current')#当前选中
        按标识=取字段(快照,'byId') or {}#行表
        if 当前 is None or 按标识.get(当前) is None or 当前==自身._监视中:#无选中、不在表、或已是舞台
            return#掩盖缺口保住舞台
        自身._监视中=当前#记下新舞台
        自身._扫推迟拆除()#扫上一舞台推迟的拆除
        记录=自身._解析(当前)#确保有作用域
        if 记录 is not None:#有记录
            火忘(记录['session'].打开())#打开历史窗口
            火忘(自身._管理器.刷新子智能体(当前))#刷新子名册

    def _解析(自身,标识):#惰性铸造作用域
        """为合格会话惰性铸造作用域 + 绑定。"""
        已有=自身._作用域们.get(标识)#已有则复用
        if 已有 is not None:#身份稳定
            return 已有#复用
        if not 自身._合格(标识):#不合格不铸造
            return None#无记录
        句柄=铸造作用域(自身._根上下文,标识)#铸造光纤与上下文
        光纤=取字段(句柄,'fiber')#光纤
        上下文=取字段(句柄,'ctx')#上下文
        会话对象=自身._管理器.取得(标识)#取出对象层实例
        会话对象.绑定作用域(上下文)#绑上作用域
        装配={'sessionId':标识,'session':会话对象,'ctx':上下文}#对外绑定
        记录={#完整记录
            'fiber':光纤,#光纤
            'ctx':上下文,#上下文
            'binding':装配,#绑定
            'session':会话对象,#具体会话
            'provideInfo':自身._提供通道.物化信息(装配),#物化标准道具
        }#结束记录
        自身._作用域们[标识]=记录#登记
        return 记录#交给调用方

    def _合格(自身,标识):#是否该有作用域
        """作用域铸造与修剪共用的唯一存活判断：宿主已列出或当前已寻址。"""
        快照=自身.list.取快照()#列表与当前
        标识们=取字段(快照,'ids') or []#列表 id
        return 取字段(快照,'current')==标识 or 标识 in 标识们#当前或在列表里

    def _投影列表(自身):#管理器 → 列表存储
        """把管理器的列表快照投影进存储（标题推导只用于展示）。"""
        管理快照=自身._管理器.取列表快照()#对象层真相
        条目们=取字段(管理快照,'items') or ()#行
        当前=取字段(管理快照,'current')#当前
        阶段=取字段(管理快照,'phase')#阶段
        名册按父=取字段(管理快照,'subagentsByParent') or {}#名册
        任务按会话=取字段(管理快照,'jobsBySession') or {}#任务
        当前地址=取字段(管理快照,'currentAddress')#地址
        标识们=[]#列表 id
        按标识={}#按 id 的行
        for 条目 in 条目们:#每条宿主行
            会话标识=取字段(条目,'sessionId')#id
            标识们.append(会话标识)#列入顺序
            摘要={#投影摘要
                'id':会话标识,#id
                'displayTitle':展示标题于(取字段(条目,'title'),取字段(条目,'cwd'),会话标识),#展示标题
                'running':取字段(条目,'running'),#是否在跑
                'blank':取字段(条目,'blank'),#空白位
                'updatedAt':取字段(条目,'updatedAt'),#更新时间
            }#结束基础
            if 取字段(条目,'completed'):#完成才带
                摘要['completed']=True#完成标记
            if 取字段(条目,'pendingInteraction') is not None:#有挂起
                摘要['pendingInteraction']=取字段(条目,'pendingInteraction')#挂起交互
            if 取字段(条目,'projectionValues') is not None:#有投影
                摘要['projectionValues']=取字段(条目,'projectionValues')#投影值
            if 取字段(条目,'title') is not None:#可选标题
                摘要['title']=取字段(条目,'title')#标题
            if 取字段(条目,'cwd') is not None:#可选 cwd
                摘要['cwd']=取字段(条目,'cwd')#工作目录
            if 取字段(条目,'parentSessionId') is not None:#可选父
                摘要['parentId']=取字段(条目,'parentSessionId')#父 id
            if 取字段(条目,'origin') is not None:#可选来源
                摘要['origin']=取字段(条目,'origin')#来源
            if 取字段(条目,'agentPreset') is not None:#可选预设
                摘要['agentPreset']=取字段(条目,'agentPreset')#预设
            按标识[会话标识]=摘要#写入
        if 当前 is not None and 当前地址 is not None:#当前是寻址子智能体
            已见=set()#防环
            地址=当前地址#沿父链上走
            while 地址 is not None and 取字段(地址,'childSessionId') not in 已见:#未见过的子
                子标识=取字段(地址,'childSessionId')#子 id
                已见.add(子标识)#记下
                父标识=取字段(地址,'parentSessionId')#父 id
                父名册=名册按父.get(父标识) if isinstance(名册按父,dict) else None#父名册
                子行=None#名册条目
                for 条目 in (取字段(父名册,'entries') or [] if 父名册 is not None else []):#找该子
                    if 取字段(条目,'kind')=='child' and 取字段(条目,'id')==子标识:#命中
                        子行=条目#记下
                        break#停
                if 取字段(子行,'kind')!='child':#名册对不上则停
                    break#停
                展示=取字段(子行,'label')#标签
                if 展示 is None:#无标签
                    展示=子标识#用 id
                摘要=按标识.get(子标识)#是否已有宿主行
                if 摘要 is None:#面包屑专用行
                    按标识[子标识]={#补一条不进 ids 的摘要
                        'id':子标识,#子 id
                        'displayTitle':展示,#展示名
                        'parentId':父标识,#父
                        'origin':'subagent',#来源
                        'running':取字段(子行,'activity')=='running',#名册活动
                        'blank':False,#子项不是空白会话
                        'updatedAt':0,#无宿主更新时间
                    }#结束补行
                elif 取字段(摘要,'displayTitle')!=展示:#已有行但标题不同
                    新摘要=dict(摘要)#拷贝
                    新摘要['displayTitle']=展示#用名册标签覆盖展示
                    按标识[子标识]=新摘要#写回
                父摘要=按标识.get(父标识)#父摘要
                if 父摘要 is not None and 取字段(父摘要,'origin')!='subagent':#走到普通会话则停
                    break#停
                地址=自身._管理器.导航地址(父标识)#继续向上
        已持久=取字段(自身._选择.取快照(),'sessionId')#已持久的 id
        if 当前 is None:#无当前
            if 已持久 is not None:#擦持久
                自身._选择.设({})#擦掉持久格
        else:#有当前
            选择快照=自身._选择.取快照()#再读选择
            持久地址=取字段(选择快照,'subagentAddress')#持久子地址
            if (按标识.get(当前) is not None#当前在表里
                and (已持久!=当前#id 变了
                    or 取字段(持久地址,'childSessionId')!=取字段(当前地址,'childSessionId')#子变了
                    or 取字段(持久地址,'parentSessionId')!=取字段(当前地址,'parentSessionId')#父变了
                    or 取字段(持久地址,'mode')!=取字段(当前地址,'mode'))):#模式变了
                下一选择={'sessionId':当前}#写下持久选择
                if 当前地址 is not None:#有地址才带
                    下一选择['subagentAddress']=当前地址#子智能体地址
                自身._选择.设(下一选择)#持久化
        自身.list.设({#发布列表快照
            'ids':标识们,#列表 id
            'byId':按标识,#按 id 的行
            'current':当前,#当前选中
            'phase':阶段,#列表阶段
            'subagentsByParent':名册按父,#名册
            'jobsBySession':任务按会话,#任务
            'currentAddress':当前地址,#当前地址
        })#结束 set
        自身._修剪作用域()#按合格判断修剪作用域

    def _修剪作用域(自身):#修剪作用域
        """拆掉已不合格且不在舞台上的作用域 + 实例；staged 的推迟到舞台挪走。"""
        for 标识,记录 in list(自身._作用域们.items()):#每个已铸造
            if 自身._合格(标识):#仍合格则留
                continue#下一项
            if 标识==自身._监视中:#在舞台上
                自身._推迟拆除.add(标识)#推迟拆除
                continue#先不拆
            自身._作用域们.pop(标识,None)#从表去掉
            自身._推迟拆除.discard(标识)#若曾推迟也清掉
            自身._拆除作用域(标识,记录)#真正拆除

    def _拆除作用域(自身,标识,记录):#拆除一个作用域
        """整条按会话轴的一次拆除：作用域光纤、槽位按会话存储、Session 实例。"""
        光纤=取字段(记录,'fiber')#光纤
        拆除=getattr(光纤,'dispose',None) if 光纤 is not None else None#dispose
        if callable(拆除):#有拆除
            拆除()#拆光纤
        取字段(记录,'session').解绑作用域()#解绑作用域
        槽位=自身._根上下文.get('slots') if hasattr(自身._根上下文,'get') else None#可选槽位服务
        修剪=getattr(槽位,'pruneStoreScope',None) if 槽位 is not None else None#按会话修剪
        if callable(修剪):#有槽位则修剪
            修剪(标识)#修剪其按会话存储
        自身._管理器.丢掉(标识)#丢掉对象层实例

    def _扫推迟拆除(自身):#扫推迟拆除
        """跑掉会话已不在舞台上的推迟拆除（舞台挪走时调用）。"""
        for 标识 in list(自身._推迟拆除):#快照后遍历
            if 标识==自身._监视中:#新舞台自己不拆
                continue#跳过
            if 自身._合格(标识):#又合格了
                自身._推迟拆除.discard(标识)#取消推迟
                continue#留下作用域
            记录=自身._作用域们.get(标识)#取出记录
            自身._推迟拆除.discard(标识)#出推迟集
            if 记录 is not None:#仍有记录
                自身._作用域们.pop(标识,None)#从表去掉
                自身._拆除作用域(标识,记录)#拆除
