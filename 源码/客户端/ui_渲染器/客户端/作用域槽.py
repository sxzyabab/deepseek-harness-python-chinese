from ...ui_槽位 import 过期授权错误,槽位所有权错误#错误与命名
from .登记表 import 标准钩子属性名#钩子命名
from .绑定 import (#内部绑定
    宿主栈,根标准提供者,作用域提供者,槽组装错误,
    键控可观察钩子,可缺席可观察钩子,可观察钩子,用宿主,用根绑定,用作用域绑定,
)#绑定结束

__all__=['创建槽渲染器','槽错误边界','槽出口','根出口','槽渲染器']#仅中文公开名

空注入属性={}#空注入
空槽注入={'props':空注入属性}#空调度注入
锚点样式={'display':'contents'}#锚点样式
首化身={'adopted':None,'epoch':0}#首化身

渲染槽缓存={}#renderSlot 缓存（id 近似 WeakMap）
渲染链缓存={}#链绑定缓存
根注入缓存={}#根 inject 缓存
会话注入缓存={}#会话 inject
可选会话注入缓存={}#可选会话
槽注入缓存={}#调度方 inject 缓存
文案座位缓存={}#t 座位缓存
文案订阅缓存={}#locale 订阅缓存
条目键表={}#条目→key
下一条目键=0#条目 key 序号
根标准缓存={}#根标准缓存
会话标准缓存={}#会话标准
可选标准缓存={}#可选标准
作用域区域缓存={}#区域提供者缓存

def 空监听():
    """仅驱动重读的占位订阅回调。"""
    return None#无

def 绑定渲染槽(宿主,条目):
    """按条目身份稳定；死亡后抛过期授权。条目为 dict。"""
    键=id(条目)#缓存键
    绑定=渲染槽缓存[键] if 键 in 渲染槽缓存 else None#读缓存
    if 绑定 is None:#未缓存
        def 闭包(子键,拥有方,选项=None):
            """子声明检查。"""
            if 宿主.isLive(条目) is False:#条目已死
                raise 过期授权错误("renderSlot('"+str(子键)+"') from a disposed registration")#过期授权
            子表=条目['children'] if 'children' in 条目 and 条目['children'] is not None else {}#子声明
            声明=子表[子键] if 子键 in 子表 else None#声明
            if 声明 is None:#未声明
                raise 槽位所有权错误("slot '"+str(子键)+"' is not declared by this entry's children")#所有权错误
            种类=声明['kind'] if 'kind' in 声明 else None#种类
            if 种类=='chain':#链槽
                raise 槽位所有权错误("slot '"+str(子键)+"' is declared 'chain' — use renderSlotChain")#应用链 API
            return 槽出口(子键,拥有方,选项).渲染()#渲染出口
        绑定=闭包#写入形
        渲染槽缓存[键]=绑定#写入
    return 绑定#返回

def 绑定渲染槽链(宿主,条目):
    """按条目身份稳定。"""
    键=id(条目)#缓存键
    绑定=渲染链缓存[键] if 键 in 渲染链缓存 else None#读缓存
    if 绑定 is None:#未缓存
        def 闭包(子键,拥有方,选项=None):
            """必须是 chain。"""
            if 宿主.isLive(条目) is False:#条目已死
                raise 过期授权错误("renderSlotChain('"+str(子键)+"') from a disposed registration")#过期授权
            子表=条目['children'] if 'children' in 条目 and 条目['children'] is not None else {}#子声明
            声明=子表[子键] if 子键 in 子表 else None#声明
            if 声明 is None:#未声明
                raise 槽位所有权错误("slot '"+str(子键)+"' is not declared by this entry's children")#所有权错误
            种类=声明['kind'] if 'kind' in 声明 else None#种类
            if 种类!='chain':#非链
                raise 槽位所有权错误("slot '"+str(子键)+"' is declared '"+str(种类)+"', not 'chain' — use renderSlot")#应用普通 API
            return 槽出口(子键,拥有方,选项).渲染()#渲染出口
        绑定=闭包#写入形
        渲染链缓存[键]=绑定#写入
    return 绑定#返回

def 绑定注入源(面):
    """hooks/keyedHooks 变成钩子座位。面为 dict。"""
    源表=面['hooks'] if 'hooks' in 面 else None#普通源
    键控源=面['keyedHooks'] if 'keyedHooks' in 面 else None#键控源
    if 源表 is None and 键控源 is None:#无需绑定
        return 面#原样
    绑定={键:值 for 键,值 in 面.items() if 键 not in ('hooks','keyedHooks')}#剩余 props
    if 源表 is not None:#有普通源
        for 名称,源 in 源表.items():#逐普通源
            绑定[标准钩子属性名(名称)]=可观察钩子(源)#普通钩子座位
    if 键控源 is not None:#有键控
        for 名称,源 in 键控源.items():#逐键控源
            绑定[标准钩子属性名(名称)]=键控可观察钩子(源)#键控钩子座位
    return 绑定#返回

def 执行注入(条目,绑定,动作):
    """声明派生的位置参数。"""
    if 'inject' not in 条目:#无工厂
        return 空注入属性#空
    注入=条目['inject']#工厂
    if 注入 is None:#空
        return 空注入属性#空
    参数=[]#位置参数
    if 绑定 is not None:#有绑定
        参数.append(绑定['key'] if 'key' in 绑定 else None)#会话键
    if 动作 is not None:#有 actions
        参数.append(动作)#store actions
    return 绑定注入源(注入(*参数))#绑定源

def 缓存槽注入(面):
    """按稳定对象身份规范化。面为 dict。"""
    if 面 is None:#无面
        return 空槽注入#空
    键=id(面)#缓存键
    已=槽注入缓存[键] if 键 in 槽注入缓存 else None#读缓存
    if 已 is not None:#命中
        return 已#返回
    定义=面['hooks'] if 'hooks' in 面 else None#钩子定义
    if 定义 is None:#无 hooks
        已={'props':面}#整面当 props
        槽注入缓存[键]=已#写入
        return 已#返回
    属性={键名:值 for 键名,值 in 面.items() if 键名!='hooks'}#剩余
    工厂表=None#延迟工厂表
    for 名称,定义项 in 定义.items():#逐定义
        钩名=标准钩子属性名(名称)#标准名
        if callable(定义项):#延迟工厂；上游 HookDef = Observable | factory
            if 工厂表 is None:#懒建表
                工厂表={}#表
            工厂表[名称]=定义项#延迟工厂
        else:#可观察源
            属性[钩名]=可观察钩子(定义项)#绑钩子
    已={'props':属性} if 工厂表 is None else {'props':属性,'slotHookFactories':工厂表}#含工厂
    槽注入缓存[键]=已#写入
    return 已#返回

def 缓存根注入(条目,动作):
    """按条目缓存。"""
    键=id(条目)#缓存键
    属性=根注入缓存[键] if 键 in 根注入缓存 else None#读缓存
    if 属性 is None:#未命中
        属性=执行注入(条目,None,动作)#跑 inject
        根注入缓存[键]=属性#写入
    return 属性#返回

def 缓存会话注入(条目,绑定,动作):
    """按（条目 × 绑定）缓存。"""
    外键=id(条目)#按条目
    if 外键 not in 会话注入缓存:#无
        会话注入缓存[外键]={}#建
    外=会话注入缓存[外键]#按条目
    内键=id(绑定)#按绑定
    属性=外[内键] if 内键 in 外 else None#读
    if 属性 is None:#未命中
        属性=执行注入(条目,绑定,动作)#跑 inject
        外[内键]=属性#写入
    return 属性#返回

def 缓存可选会话注入(条目,绑定,动作):
    """按（条目 × 绑定）缓存。"""
    外键=id(条目)#按条目
    if 外键 not in 可选会话注入缓存:#无
        可选会话注入缓存[外键]={}#建
    外=可选会话注入缓存[外键]#按条目
    内键=id(绑定)#按绑定
    属性=外[内键] if 内键 in 外 else None#读
    if 属性 is None:#未命中
        属性=执行注入(条目,绑定,动作)#跑 inject
        外[内键]=属性#写入
    return 属性#返回

def 文案座位(面,命名空间):
    """按（面, 命名空间, 修订）缓存。locale 面为对象。"""
    面键=id(面)#按面
    if 面键 not in 文案座位缓存:#无
        文案座位缓存[面键]={}#建
    按面=文案座位缓存[面键]#按面
    快照=面.getSnapshot()#快照为 dict
    修订=快照['revision'] if 'revision' in 快照 else None#当前修订
    缓存=按面[命名空间] if 命名空间 in 按面 else None#按命名空间
    if 缓存 is not None and 缓存['revision']==修订:#同修订
        return 缓存['t']#复用
    绑定=面.bind(命名空间)#绑定命名空间
    def 翻译(键,参数=None):
        """每修订新包装。"""
        return 绑定(键,参数)#调用
    按面[命名空间]={'revision':修订,'t':翻译}#写入缓存
    return 翻译#返回

def 文案订阅(面):
    """逐面 subscribe/getSnapshot 闭包对。locale 面为对象。"""
    键=id(面)#缓存键
    缓存=文案订阅缓存[键] if 键 in 文案订阅缓存 else None#读缓存
    if 缓存 is None:#未建
        def 订面(回调):
            """订阅 locale 面。"""
            return 面.subscribe(回调)#订
        def 取修订():
            """读修订。"""
            快照=面.getSnapshot()#快照
            return 快照['revision'] if 'revision' in 快照 else None#修订
        缓存={'subscribe':订面,'getRevision':取修订}#闭包对
        文案订阅缓存[键]=缓存#写入
    return 缓存#返回

def 用文案修订(面):
    """未安装时为 0。"""
    if 面 is None:#无面
        return 0#版本 0
    return 文案订阅(面)['getRevision']()#读修订

def 条目键于(条目):
    """按条目身份稳定。"""
    global 下一条目键#序号
    标识=id(条目)#身份
    键=条目键表[标识] if 标识 in 条目键表 else None#读缓存
    if 键 is None:#未分配
        键=下一条目键#递增
        下一条目键+=1#加一
        条目键表[标识]=键#写入
    return 键#返回

def 行顺序(项):
    """list 行按 order 排。"""
    return 项['order']#序

class 槽错误边界:
    """组装错误穿透；其它失败显示崩溃面。"""
    def __init__(自身,槽键,条目错误时,子树=None):
        """记下槽键与回调。子树为 thunk。"""
        自身.slotKey=槽键#槽键
        自身.onEntryError=条目错误时#崩溃回调
        自身.子树=子树#子节点
        自身.失败=False#初始未失败

    def 渲染(自身):
        """失败则崩溃面。"""
        if 自身.失败 is True:#已失败
            return {'type':'slot-error','slotKey':自身.slotKey}#崩溃面
        try:#尝试子树
            return 自身.子树()#thunk
        except 槽组装错误:#组装错误穿透
            raise#再抛
        except Exception as 错误:#登记方崩溃
            print("槽条目在 '"+自身.slotKey+"' 崩溃:",错误)#打印
            自身.失败=True#标记失败
            自身.onEntryError(错误)#上报
            return {'type':'slot-error','slotKey':自身.slotKey}#崩溃面

def 物化标准绑定(绑定,可选):
    """把一个绑定物化为稳定的框架钩子与普通 prop 座位。绑定为 dict。"""
    属性=绑定['props'] if 'props' in 绑定 and 绑定['props'] is not None else {}#拷贝 prop
    标准=dict(属性)#拷
    钩子表=绑定['hooks'] if 'hooks' in 绑定 and 绑定['hooks'] is not None else {}#钩子
    for 名称,源 in 钩子表.items():#逐钩子
        if 源 is None and 可选 is False:#严格缺源
            raise 槽组装错误("strict standard hook '"+str(名称)+"' has no source")#抛错
        标准[标准钩子属性名(名称)]=可缺席可观察钩子(源) if 可选 is True else 可观察钩子(源)#钩子
    键控表=绑定['keyedHooks'] if 'keyedHooks' in 绑定 and 绑定['keyedHooks'] is not None else {}#键控
    for 名称,源 in 键控表.items():#逐键控
        if 源 is None and 可选 is False:#严格缺源
            raise 槽组装错误("strict keyed standard hook '"+str(名称)+"' has no source resolver")#抛错
        标准[标准钩子属性名(名称)]=键控可观察钩子(源)#键控钩子
    return 标准#返回

def 标准属性(作用域,根绑定,作用域绑定):
    """上下文钩子工厂使用的稳定官方 props 对象。"""
    根键=id(根绑定)#根
    根=根标准缓存[根键] if 根键 in 根标准缓存 else None#根缓存
    if 根 is None:#未命中
        根=物化标准绑定(根绑定,False)#物化根
        根标准缓存[根键]=根#写入
    if 作用域=='root':#仅根
        return 根#返回
    if 作用域绑定 is None:#缺绑定
        raise 槽组装错误("scope '"+str(作用域)+"' rendered without a standard-source binding")#抛错
    缓存轴=会话标准缓存 if 作用域=='session' else 可选标准缓存#选缓存轴
    if 根键 not in 缓存轴:#无
        缓存轴[根键]={}#建
    按根=缓存轴[根键]#按根
    域键=id(作用域绑定)#按作用域
    标准=按根[域键] if 域键 in 按根 else None#按作用域
    if 标准 is not None:#命中
        return 标准#返回
    标准={**根,**物化标准绑定(作用域绑定,作用域=='session-maybe')}#合并
    按根[域键]=标准#写入
    return 标准#返回

def 作用域区域提供者(适配器):
    """把域自有作用域区域渲染器绑到当前作用域绑定。适配器为 dict。"""
    键=id(适配器)#缓存键
    提供者=作用域区域缓存[键] if 键 in 作用域区域缓存 else None#读缓存
    if 提供者 is not None:#命中
        return 提供者#返回
    if 'renderArea' not in 适配器:#无
        raise 槽组装错误("scope 'session' adapter does not provide its area renderer")#抛错
    渲区=适配器['renderArea']#渲染器
    if 渲区 is None:#空
        raise 槽组装错误("scope 'session' adapter does not provide its area renderer")#抛错
    def 区域提供者组件(属性):
        """当前绑定 + props。"""
        return 渲区(用作用域绑定(),属性)#渲染
    作用域区域缓存[键]=区域提供者组件#写入
    return 区域提供者组件#返回

def 标准工具包(宿主,条目,作用域,根绑定,作用域绑定):
    """标准座位 + locale/store/renderSlot/SessionProvider。"""
    标准=标准属性(作用域,根绑定,作用域绑定)#标准座位
    包=dict(标准)#工具包起点
    文案名=条目['locale'] if 'locale' in 条目 else None#声明了文案
    if 文案名 is not None:#有
        面=宿主.locale()#locale 面；未装为 None
        if 面 is None:#未安装
            raise 槽组装错误("entry declares locale namespace '"+str(文案名)+"' but no locale face is installed (locale plugin missing from the composition?)")#抛错
        包['t']=文案座位(面,文案名)#t 座位
    作用域键=作用域绑定['key'] if 作用域绑定 is not None and 'key' in 作用域绑定 else None#键
    作用域存储绑定=作用域绑定 if 作用域键 is not None else None#有键可解析
    存储=宿主.storeOf(条目,作用域存储绑定)#解析
    动作=None#actions
    if 存储 is not None:#有 store；实例为对象
        包['useStore']=可观察钩子(存储)#useStore 座位
        动作=存储.actions#actions
        包['actions']=动作#actions 座位
    子表=条目['children'] if 'children' in 条目 else None#有子声明
    if 子表 is not None:#有；空 dict 在 JS 为真
        包['renderSlot']=绑定渲染槽(宿主,条目)#renderSlot 座位
        if any(规格['kind']=='chain' for 规格 in 子表.values() if 'kind' in 规格):#含链
            包['renderSlotChain']=绑定渲染槽链(宿主,条目)#链座位
        if any(规格['scope']=='session' for 规格 in 子表.values() if 'scope' in 规格):#含会话子
            适配器=宿主.scope('session')#取适配器
            if 适配器 is None:#未安装
                raise 槽组装错误("entry declares a session child without an installed 'session' scope adapter")#抛错
            包['SessionProvider']=作用域区域提供者(适配器)#SessionProvider 座位
    return {'kit':包,'standard':标准,'actions':动作}#返回三件套

def 绑定槽钩子工厂(工厂表,标准,钩子上下文):
    """为一个稳定的 renderSlot 出现点绑定。"""
    钩子={}#结果表
    for 名称,工厂 in 工厂表.items():#逐工厂
        钩子[标准钩子属性名(名称)]=工厂(标准,钩子上下文)#调用工厂
    return 钩子#返回

def 渲染条目(槽键,组件,包,标准,注入,槽注入,拥有方,钩子上下文,有钩子上下文):
    """无延迟工厂则直接展开；组件为函数。"""
    工厂表=槽注入['slotHookFactories'] if 'slotHookFactories' in 槽注入 else None#延迟工厂
    槽属性=槽注入['props'] if 'props' in 槽注入 else {}#inject props
    合并={**包,**注入,**槽属性,**拥有方}#展开
    if 工厂表 is None:#无延迟工厂
        return 组件(合并)#直接展开
    if 有钩子上下文 is False:#缺上下文
        raise 槽组装错误("slot '"+str(槽键)+"' has contextual injected Hooks but no hookContext")#抛错
    上下文钩=绑定槽钩子工厂(工厂表,标准,钩子上下文)#绑工厂
    合并={**合并,**上下文钩}#再合
    return 组件(合并)#展开

def 渲染条目体(宿主,条目,作用域,绑定,槽键,槽注入,拥有方,钩子上下文,有钩子上下文):
    """根/会话/可选会话共用。"""
    根绑定=用根绑定()#根绑定
    组件=条目['component']#组件
    三件=标准工具包(宿主,条目,作用域,根绑定,绑定)#工具包
    if 作用域=='root':#根
        注入=缓存根注入(条目,三件['actions'])#根 inject
    elif 作用域=='session':#严格会话
        注入=缓存会话注入(条目,绑定,三件['actions'])#会话 inject
    else:#可选会话
        注入=缓存可选会话注入(条目,绑定,三件['actions'])#可选 inject
    return 渲染条目(槽键,组件,三件['kit'],三件['standard'],注入,槽注入,拥有方,钩子上下文,有钩子上下文)#渲染

class 可选会话条目:
    """收养——唯一行为；身份在 undefined → 首个 id 上保持。"""
    def __init__(自身,条目,拥有方,槽键,槽注入,钩子上下文,有钩子上下文):
        """记下 props 与化身记账。"""
        自身.entry=条目#条目
        自身.ownerProps=拥有方#拥有方
        自身.slotKey=槽键#槽键
        自身.slotInjected=槽注入#inject
        自身.hookContext=钩子上下文#上下文
        自身.hasHookContext=有钩子上下文#门闩
        自身.state=dict(首化身)#化身记账

    def 渲染(自身):
        """按 epoch 重挂体。"""
        宿主=用宿主()#宿主
        绑定=用作用域绑定()#当前绑定
        收养=自身.state['adopted']#已收养
        代数=自身.state['epoch']#化身代数
        键=绑定['key'] if 'key' in 绑定 else None#当前键
        if 键 is not None and 收养 is None:#首次收养
            收养=键#记下收养
            自身.state={'adopted':收养,'epoch':代数}#写回
        elif 收养 is not None and 键 is not None and 键!=收养:#切换会话
            收养=键#新收养
            代数+=1#下一化身
            自身.state={'adopted':收养,'epoch':代数}#写回
        elif 收养 is not None and 键 is None:#回到无会话
            收养=None#清空
            代数+=1#下一化身
            自身.state={'adopted':收养,'epoch':代数}#写回
        return {#按 epoch 重挂体
            'type':'session-maybe-entry',#类型
            'epoch':代数,#化身键
            'body':渲染条目体(宿主,自身.entry,'session-maybe',绑定,自身.slotKey,自身.slotInjected,自身.ownerProps,自身.hookContext,自身.hasHookContext),#体
        }#树结束

def 渲染链结果(槽键,当选,选项):
    """同时保留覆盖层回退的树位置。选项为 dict 或 None。"""
    回退=选项['fallback'] if 选项 is not None and 'fallback' in 选项 else None#回退
    覆盖=选项['overlay'] is True if 选项 is not None and 'overlay' in 选项 else False#覆盖层
    if 覆盖 is False:#无覆盖层
        return 当选 if 当选 is not None else 回退#无覆盖层
    return {#覆盖层布局
        'type':'chain-overlay',#类型
        'slotKey':槽键,#槽键
        'fallbackVisible':当选 is None,#有当选则隐藏回退
        'fallback':回退,#回退内容
        'elected':当选,#当选
    }#树结束

def 条目选项键(条目):
    """options.key。"""
    形=条目['options'] if 'options' in 条目 else {}#形状
    return 形['key'] if 'key' in 形 else None#键

def 条目选项标识(条目):
    """options.id。"""
    形=条目['options'] if 'options' in 条目 else {}#形状
    return 形['id'] if 'id' in 形 else None#id

def 条目选项顺序(条目):
    """options.order；缺键为 0。上游 ?? 0，0 合法。"""
    形=条目['options'] if 'options' in 条目 else {}#形状
    return 形['order'] if 'order' in 形 else 0#缺键才 0

def 渲染出口内容(宿主,槽键,拥有方,选项,作用域绑定):
    """锚点后的 kind 调度。"""
    规格=宿主.specOf(槽键)#规范
    if 规格 is None:#未声明
        return None#空
    种类=规格['kind'] if 'kind' in 规格 else None#种类
    仅回退=选项['fallbackOnly'] is True if 选项 is not None and 'fallbackOnly' in 选项 else False#仅回退
    if 种类=='chain' and 仅回退 is True:#仅回退
        return 渲染链结果(槽键,None,选项)#仅回退模式
    作用域=规格['scope'] if 'scope' in 规格 else None#作用域
    绑定键=作用域绑定['key'] if 作用域绑定 is not None and 'key' in 作用域绑定 else None#键
    if 作用域=='session' and 绑定键 is None:#严格会话无键
        raise 槽组装错误("strict session slot '"+str(槽键)+"' rendered without a scope binding")#抛错
    条目列表=宿主.entriesOf(槽键)#条目
    槽注入=缓存槽注入(规格['inject'] if 'inject' in 规格 else None)#调度 inject

    def 守卫(条目,键=None,拥有=None):
        """遮蔽 kind 崩溃时退位；链报告但不退位。"""
        拥有方值=拥有 if 拥有 is not None else 拥有方#拥有方
        有钩=选项 is not None and 'hookContext' in 选项#是否带上下文
        钩上下文=选项['hookContext'] if 有钩 is True else None#钩子上下文
        def 条目错误时(错误):
            """报告。"""
            宿主.reportEntryError(槽键,条目,错误,{'abdicate':种类!='chain'})#报告
        if 作用域=='session':#严格会话
            绑定=用作用域绑定()#当前绑定
            if ('key' not in 绑定) or (绑定['key'] is None):#无会话
                raise 槽组装错误("strict session slot '"+str(槽键)+"' rendered without a scope binding")#抛错
            def 会话体():
                """严格会话条目体。"""
                return 渲染条目体(用宿主(),条目,'session',绑定,槽键,槽注入,拥有方值,钩上下文,有钩)#体
            边界=槽错误边界(槽键,条目错误时,会话体)#边界
            return {'type':'strict-session-entry','key':绑定['key'],'body':边界.渲染()}#树
        if 作用域=='session-maybe':#可选会话
            def 可选体():
                """可选会话化身。"""
                return 可选会话条目(条目,拥有方值,槽键,槽注入,钩上下文,有钩).渲染()#渲
            边界=槽错误边界(槽键,条目错误时,可选体)#边界
            return {'type':'session-maybe-wrap','key':键,'body':边界.渲染()}#树
        def 根体():
            """根条目体。"""
            return 渲染条目体(用宿主(),条目,'root',None,槽键,槽注入,拥有方值,钩上下文,有钩)#体
        边界=槽错误边界(槽键,条目错误时,根体)#根边界
        return {'type':'root-entry','key':键,'body':边界.渲染()}#树

    def 干涸格():
        """每个登记都已退位的格子。"""
        return {'type':'slot-error','slotKey':槽键}#崩溃面

    if 种类=='single':#单条目
        胜出列表=宿主.entriesOfSlot(槽键)#胜出者
        条目=胜出列表[0] if len(胜出列表)>0 else None#胜出
        if 条目 is None:#无胜出
            回退=选项['fallback'] if 选项 is not None and 'fallback' in 选项 else None#回退
            return 干涸格() if len(条目列表)>0 else 回退#干涸或回退
        return 守卫(条目,条目键于(条目))#渲染胜出
    if 种类=='keyed':#键控
        条目键=选项['entryKey'] if 选项 is not None and 'entryKey' in 选项 else None#请求键
        胜出列表=宿主.entriesOfSlot(槽键)#胜出
        条目=None#命中
        for 项 in 胜出列表:#按键找
            if 条目选项键(项)==条目键:#同键
                条目=项#命中
                break#停
        if 条目 is None:#未命中
            占用=False#格是否曾占用
            for 项 in 条目列表:#扫
                if 条目选项键(项)==条目键:#占用
                    占用=True#是
                    break#停
            回退=选项['fallback'] if 选项 is not None and 'fallback' in 选项 else None#回退
            return 干涸格() if 占用 is True else 回退#干涸或回退
        return 守卫(条目,条目键于(条目))#渲染
    if 种类=='chain':#链选举
        当选=None#当选节点
        for 条目 in 条目列表:#逐条选举
            try:#跑选择器
                选择=条目['select'] if 'select' in 条目 else None#选择器
                命中=选择(拥有方) if 选择 is not None else None#纯选择；select 为函数
            except Exception as 错误:#选择器抛错
                登记方=条目['registrant'] if 'registrant' in 条目 and 条目['registrant'] is not None else 'unknown registrant'#登记方
                print("链选择器在 '"+str(槽键)+"' ("+str(登记方)+") 崩溃，视为谢绝:",错误)#打印并谢绝
                continue#下一条
            if 命中 is not None:#命中
                当选=守卫(条目,条目键于(条目),{**拥有方,'matched':命中})#带 matched 渲染
                break#停止选举
        return 渲染链结果(槽键,当选,选项)#链结果
    胜出列表=宿主.entriesOfSlot(槽键)#胜出行
    行列表=[]#活行
    行标识=set()#已有 id
    for 条目 in 胜出列表:#活
        标识=条目选项标识(条目)#id
        行列表.append({'entry':条目,'id':标识,'order':条目选项顺序(条目)})#活行
        行标识.add(标识)#记
    for 条目 in 条目列表:#补干涸格
        标识=条目选项标识(条目)#id
        if 标识 in 行标识:#已有
            continue#跳过
        行标识.add(标识)#登记
        行列表.append({'entry':None,'id':标识,'order':条目选项顺序(条目)})#干涸行
    行列表.sort(key=行顺序)#按 order 排
    仅=选项['only'] if 选项 is not None and 'only' in 选项 else None#可选 id 过滤
    if 仅 is not None:#过滤
        行列表=[项 for 项 in 行列表 if 项['id']==仅]#过滤
    if len(行列表)==0:#空列表
        return 选项['fallback'] if 选项 is not None and 'fallback' in 选项 else None#回退
    项视=[]#行
    for 项 in 行列表:#逐行
        if 项['entry'] is not None:#胜出
            项视.append(守卫(项['entry'],'e'+str(条目键于(项['entry']))))#守卫
        else:#干涸
            项视.append({'type':'slot-error','slotKey':槽键,'key':'x'+str(项['id'])})#干涸
    return {'type':'slot-list','items':项视}#列表片段

class 槽出口:
    """每个槽渲染点暴露稳定的 data-slot 包装。"""
    def __init__(自身,槽键,拥有方,选项=None):
        """记下键与 props。"""
        自身.slotKey=槽键#槽键
        自身.ownerProps=拥有方#拥有方
        自身.opts=选项#渲染选项

    def 渲染(自身):
        """锚点包装 + 调度内容。"""
        宿主=用宿主()#宿主
        宿主.subscribe(自身.slotKey,空监听)#订变更（驱动重读）
        宿主.getVersion(自身.slotKey)#读版本
        用文案修订(宿主.locale())#订 locale
        作用域绑定=用作用域绑定()#作用域绑定
        return {#锚点包装
            'type':'slot-outlet',#类型
            'slotKey':自身.slotKey,#锚点
            'style':锚点样式,#样式
            'content':渲染出口内容(宿主,自身.slotKey,自身.ownerProps,自身.opts,作用域绑定),#调度内容
        }#树结束

class 根出口:
    """外壳唯一的 ctx 级渲染入口。"""
    def __init__(自身,拥有方):
        """记下拥有方。"""
        自身.ownerProps=拥有方#拥有方

    def 渲染(自身):
        """未登记的 root 是启动顺序失败。"""
        宿主=用宿主()#宿主
        宿主.subscribe('root',空监听)#订
        宿主.getVersion('root')#版本
        用文案修订(宿主.locale())#订 locale
        胜出列表=宿主.entriesOfSlot('root')#根胜出
        条目=胜出列表[0] if len(胜出列表)>0 else None#胜出
        if 条目 is None:#无胜出
            if len(宿主.entriesOf('root'))>0:#有登记但全部退位
                return {'type':'slot-error','slotKey':'root'}#干涸崩溃
            raise 槽组装错误("renderSlot('root') before any 'root' registration (boot order)")#启动顺序
        def 条目错误时(错误):
            """报告。"""
            宿主.reportEntryError('root',条目,错误,{'abdicate':True})#退位
        def 根体():
            """根条目体。"""
            return 渲染条目体(宿主,条目,'root',None,'root',空槽注入,自身.ownerProps,None,False)#体
        边界=槽错误边界('root',条目错误时,根体)#根边界
        return {#根锚点
            'type':'root-outlet',#类型
            'slotKey':'root',#根锚点
            'style':锚点样式,#样式
            'key':条目键于(条目),#条目 key
            'body':边界.渲染(),#体
        }#树结束

class 槽渲染器:
    """安装进 SlotRegistry 的渲染器。"""
    def renderRoot(自身,宿主,拥有方):
        """提供者树。"""
        宿主栈.append(宿主)#压宿主
        try:#渲
            def 包根出口():
                """ScopeProvider session-maybe。"""
                return 根出口(拥有方).渲染()#根
            def 子树():
                """可选会话包根出口。"""
                return 作用域提供者('session-maybe',包根出口).渲染()#可选会话
            return {#提供者树
                'type':'slot-renderer-root',#类型
                'tree':根标准提供者(子树).渲染(),#根源
            }#树结束
        finally:#出栈
            宿主栈.pop()#出栈

def 创建槽渲染器():
    """构建安装进 SlotRegistry 的渲染器。"""
    return 槽渲染器()#实例
