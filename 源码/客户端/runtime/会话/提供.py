"""会话标准 props 的 provide 通道：提供方名册、包物化、静态无会话投影与当前投影可观察。

对齐上游 `runtime/src/client/sessions/provide.ts`。公开面仅中文名。
一份实现 — SessionRuntime 从线上事实驱动它，测试运行时的 sessions 替身从夹具驱动它 —
因此物化规则与投影语义不能在生产与测试台之间漂移。

依赖未迁：`.服务`（会话装配句柄 SessionBinding、提供方描述 SessionProvideDescriptor）；
`dsh-client-ui-slots`（HostObservable、SessionMaybeProvideInfo、SessionProvideInfo）。
本叶以鸭式映射/可调用表达上述类型能承载的通道行为。
"""
import warnings#订阅者失败诊断

__all__=['会话提供通道宿主','会话提供通道']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 有自有键(对象,键):#自有键判定
    """对齐 Object.hasOwn：映射看键，其余看属性字典。"""
    if isinstance(对象,dict):#映射
        return 键 in 对象#自有键
    return 键 in getattr(对象,'__dict__',{})#实例自有

class 会话提供通道宿主:#通道宿主协议
    """拥有方侧钩：通道如何够到拥有方的活包与当前选择。

    拥有方须实现 重建包 / 解析当前（鸭式，不必继承本类）。
    """

    def 重建包(自身):#重建已物化包
        """按新名册重新物化每一个已经物化过的包。

        惰性物化的会话在首次解析时捡起新名册。
        """
        raise NotImplementedError('会话提供通道宿主.重建包')#协议槽

    def 解析当前(自身):#当前选择的包
        """解析当前选择的包（拥有方的 maybe-provide 查找）。"""
        raise NotImplementedError('会话提供通道宿主.解析当前')#协议槽

class 会话提供通道:#provide 通道
    """提供方名册 + 物化 + 当前投影。

    通道拥有提供方贡献必须满足的每一条规则；
    拥有方只保留各自的按会话包存储，以及「当前」的定义。
    """

    def __init__(自身,宿主):#绑到拥有方
        """@param 宿主 - 拥有方侧的包存储与当前选择解析。"""
        自身._宿主=宿主#拥有方钩
        自身._提供方们=[]#提供方名册（含运行时自己的贡献）
        def 解析内建(装配):#内建 session 钩
            """每会话交出 Session 面。"""
            return {'hooks':{'session':取字段(装配,'session')}}#协议键 hooks/session
        自身._提供方们.append({#内建贡献排第一
            'hooks':['session'],#声明 session 钩
            'resolve':解析内建,#按绑定解析
        })#结束内建
        自身._可空信息缓存=自身._物化可空信息()#按当前名册建静态投影
        自身._当前快照=自身._可空信息缓存#初始当前 = 无会话投影
        自身._监听器们=set()#当前投影订阅者
        def 取快照():#读已发布快照
            """当前已发布包。"""
            return 自身._当前快照#身份稳定引用
        def 订阅(回调):#登记订阅者
            """加入集；返回取消函数。"""
            自身._监听器们.add(回调)#加入
            def 退订():#取消
                """从表删除。"""
                自身._监听器们.discard(回调)#删除
            return 退订#取消器
        自身.当前提供信息={#可观察面（协议键 getSnapshot/subscribe）
            'getSnapshot':取快照,#读快照
            'subscribe':订阅,#登记
        }#结束当前提供信息

    @property
    def 可空信息(自身):#无会话套件
        """当前名册下的静态无会话投影（已声明名字在场，值为 None）。"""
        return 自身._可空信息缓存#最近一次名册物化结果

    def 提供(自身,描述符):#登记提供方
        """登记一个按会话的标准 props 提供方。

        活包立刻重建；声明错误的提供方在注册边失败即响，且登记回滚 —
        通道从不停留在一份它无法物化的名册上。
        @param 描述符 - 静态成员名册加上按会话解析器。
        @returns 移除该提供方的 disposer。
        """
        自身._提供方们.append(描述符)#先推进名册
        try:#按新名册物化
            自身._应用名册变更()#立刻重建已物化包
        except Exception as 错误:#名册无法物化
            下标=-1#查找刚推入者
            序=0#扫描
            while 序<len(自身._提供方们):#按身份找
                if 自身._提供方们[序] is 描述符:#命中
                    下标=序#记下
                    break#停
                序+=1#下一个
            if 下标>=0:#仍在名册
                自身._提供方们.pop(下标)#回滚刚推入的提供方
            自身._应用名册变更()#按旧名册重建（推入前已成功，此处不得再抛）
            raise 错误#把物化失败抛给注册方
        def 拆除():#disposer
            """按缩小后的名册重建。"""
            下标=-1#查找位置
            序=0#扫描
            while 序<len(自身._提供方们):#按身份找
                if 自身._提供方们[序] is 描述符:#命中
                    下标=序#记下
                    break#停
                序+=1#下一个
            if 下标>=0:#仍在名册则移除
                自身._提供方们.pop(下标)#移除
            自身._应用名册变更()#按缩小后的名册重建
        return 拆除#disposer

    def 发布当前(自身):#发布当前包
        """重新推导当前选择的包，变了就发布。

        包在每次（作用域, 名册）物化时身份稳定，因此身份比较是精确的；同步通知 —
        调用点（拥有方的列表订阅、提供()）已经坐在各自的批或注册边后面。
        """
        下一个=自身._宿主.解析当前()#向拥有方要当前包
        if 下一个 is 自身._当前快照:#身份未变则不发布
            return#跳过
        自身._当前快照=下一个#记下新快照
        for 回调 in list(自身._监听器们):#拷一份，允许通知中退订
            try:#单个订阅者
                回调()#同步通知
            except Exception as 错误:#订阅者抛错
                warnings.warn('sessions.currentProvideInfo subscriber failed: '+str(错误))#诊断后继续后续监听器

    def 物化信息(自身,装配):#物化一会话的包
        """为一个会话物化标准 props 包（未声明、缺失、重复成员名失败即响）。

        @param 装配 - 喂给每个解析器的会话装配句柄。
        @returns 物化后的包（直到下一次物化之前身份稳定）。
        """
        钩表={}#已收下的钩
        道具表={}#已收下的 props
        for 描述符 in 自身._提供方们:#按名册顺序
            解析=取字段(描述符,'resolve')#按会话解析器
            贡献=解析(装配)#本提供方的贡献
            交出钩=取字段(贡献,'hooks') or {}#交出的钩，缺省空
            交出道具=取字段(贡献,'props') or {}#交出的 props，缺省空
            声明钩=list(取字段(描述符,'hooks') or [])#已声明钩名
            声明道具=list(取字段(描述符,'props') or [])#已声明 prop 名
            for 名 in (交出钩.keys() if isinstance(交出钩,dict) else []):#检查钩声明
                if 名 not in 声明钩:#交出了未声明的钩
                    raise Exception('sessions.provide: undeclared hook "'+str(名)+'"')#未声明钩
            for 名 in (交出道具.keys() if isinstance(交出道具,dict) else []):#检查 prop 声明
                if 名 not in 声明道具:#交出了未声明的 prop
                    raise Exception('sessions.provide: undeclared prop "'+str(名)+'"')#未声明 prop
            for 名 in 声明钩:#收下已声明钩
                if isinstance(交出钩,dict):#映射贡献
                    if 名 not in 交出钩 or 交出钩[名] is None:#声明了却没交（对齐 === undefined）
                        raise Exception('sessions.provide: missing hook "'+str(名)+'"')#缺失钩
                    源=交出钩[名]#该钩的源
                else:#对象贡献
                    if not 有自有键(交出钩,名) or 取字段(交出钩,名) is None:#声明了却没交
                        raise Exception('sessions.provide: missing hook "'+str(名)+'"')#缺失钩
                    源=取字段(交出钩,名)#该钩的源
                if 有自有键(钩表,名):#与先前提供方撞名
                    raise Exception('sessions.provide: duplicate hook "'+str(名)+'"')#重复钩
                钩表[名]=源#收下
            for 名 in 声明道具:#收下已声明 props
                if isinstance(交出道具,dict):#映射贡献
                    if 名 not in 交出道具:#声明了却没交（Object.hasOwn）
                        raise Exception('sessions.provide: missing prop "'+str(名)+'"')#缺失 prop
                    值=交出道具[名]#该 prop
                else:#对象贡献
                    if not 有自有键(交出道具,名):#声明了却没交
                        raise Exception('sessions.provide: missing prop "'+str(名)+'"')#缺失 prop
                    值=取字段(交出道具,名)#该 prop
                if 有自有键(道具表,名):#与先前提供方撞名
                    raise Exception('sessions.provide: duplicate prop "'+str(名)+'"')#重复 prop
                道具表[名]=值#收下
        会话=取字段(装配,'session')#对外会话面
        投影仓=取字段(会话,'projections')#投影仓库
        def 面于(键):#按键取投影面
            """从该会话投影仓库取出的按键裸值面。"""
            return 投影仓.faceOf(键)#协议键 faceOf
        return {#物化结果
            'sessionId':取字段(装配,'sessionId'),#所属会话
            'hooks':钩表,#钩表
            'props':道具表,#props 表
            'projections':{'faceOf':面于},#投影面查找（开放键空间）
        }#结束返回

    def _应用名册变更(自身):#名册变更
        """重建静态投影与拥有方的活包，然后重新发布当前那个。"""
        自身._可空信息缓存=自身._物化可空信息()#静态无会话投影
        自身._宿主.重建包()#拥有方按新名册重建活包
        自身.发布当前()#当前选择可能换了包身份

    def _物化可空信息(自身):#无会话物化
        """建造静态无会话套件，并拒绝重复的已声明名字。"""
        钩表={}#已声明钩名，值恒 None
        道具表={}#已声明 prop 名，值恒 None
        for 描述符 in 自身._提供方们:#扫名册
            for 名 in list(取字段(描述符,'hooks') or []):#声明的钩
                if 有自有键(钩表,名):#钩名冲突
                    raise Exception('sessions.provide: duplicate hook "'+str(名)+'"')#重复钩
                钩表[名]=None#占位：能力名在场，值为缺席
            for 名 in list(取字段(描述符,'props') or []):#声明的 props
                if 有自有键(道具表,名):#prop 名冲突
                    raise Exception('sessions.provide: duplicate prop "'+str(名)+'"')#重复 prop
                道具表[名]=None#占位
        return {'sessionId':None,'hooks':钩表,'props':道具表}#没有 projections 面
