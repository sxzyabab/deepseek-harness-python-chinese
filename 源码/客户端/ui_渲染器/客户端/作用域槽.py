"""声明式槽位的渲染器。逐条绑定强制子授权，条目边界吞下登记方失败。

对齐上游 `ui-renderer/src/client/scoped-slots.tsx`。公开面仅中文名。
无真 React：结构树字典 + 类边界。
"""
from ...ui_槽位 import 过期授权错误,槽位所有权错误#错误与命名
from .登记表 import 标准钩子属性名#钩子命名
from .绑定 import (#内部绑定
    宿主栈,根标准提供者,作用域提供者,槽组装错误,
    键控可观察钩子,可缺席可观察钩子,可观察钩子,用宿主,用根绑定,用作用域绑定,
)#绑定结束

__all__=['创建槽渲染器','槽错误边界','槽出口','根出口']#仅中文公开名

空注入属性={}#空注入
空槽注入={'props':空注入属性}#空调度注入
锚点样式={'display':'contents'}#锚点样式
空订阅=lambda: (lambda: None)#无面时的空订阅
零修订=lambda:0#无面时版本 0
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

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 绑定渲染槽(宿主,条目):#绑定 renderSlot
    """按条目身份稳定；死亡后抛过期授权。"""
    键=id(条目)#缓存键
    绑定=渲染槽缓存.get(键)#读缓存
    if 绑定 is None:#未缓存
        def 闭包(子键,拥有方,选项=None):#授权闭包
            """子声明检查。"""
            仍活=宿主['isLive'] if isinstance(宿主,dict) else 宿主.isLive#是否活
            if not 仍活(条目):#条目已死
                raise 过期授权错误(f"renderSlot('{子键}') from a disposed registration")#过期授权
            子们=取字段(条目,'children') or {}#子声明
            声明=子们.get(子键) if isinstance(子们,dict) else None#声明
            if 声明 is None:#未声明
                raise 槽位所有权错误(f"slot '{子键}' is not declared by this entry's children")#所有权错误
            种类=取字段(声明,'kind')#种类
            if 种类=='chain':#链槽
                raise 槽位所有权错误(f"slot '{子键}' is declared 'chain' — use renderSlotChain")#应用链 API
            return 槽出口(子键,拥有方,选项).渲染()#渲染出口
        绑定=闭包#写入形
        渲染槽缓存[键]=绑定#写入
    return 绑定#返回

def 绑定渲染槽链(宿主,条目):#绑定链
    """按条目身份稳定。"""
    键=id(条目)#缓存键
    绑定=渲染链缓存.get(键)#读缓存
    if 绑定 is None:#未缓存
        def 闭包(子键,拥有方,选项=None):#授权闭包
            """必须是 chain。"""
            仍活=宿主['isLive'] if isinstance(宿主,dict) else 宿主.isLive#是否活
            if not 仍活(条目):#条目已死
                raise 过期授权错误(f"renderSlotChain('{子键}') from a disposed registration")#过期授权
            子们=取字段(条目,'children') or {}#子声明
            声明=子们.get(子键) if isinstance(子们,dict) else None#声明
            if 声明 is None:#未声明
                raise 槽位所有权错误(f"slot '{子键}' is not declared by this entry's children")#所有权错误
            if 取字段(声明,'kind')!='chain':#非链
                raise 槽位所有权错误(f"slot '{子键}' is declared '{取字段(声明,'kind')}', not 'chain' — use renderSlot")#应用普通 API
            return 槽出口(子键,拥有方,选项).渲染()#渲染出口
        绑定=闭包#写入形
        渲染链缓存[键]=绑定#写入
    return 绑定#返回

def 绑定注入源(面):#绑定 inject 源
    """hooks/keyedHooks 变成钩子座位。"""
    源们=面.get('hooks') if isinstance(面,dict) else None#普通源
    键控源=面.get('keyedHooks') if isinstance(面,dict) else None#键控源
    if 源们 is None and 键控源 is None:#无需绑定
        return 面#原样
    绑定={键:值 for 键,值 in 面.items() if 键 not in ('hooks','keyedHooks')} if isinstance(面,dict) else {}#剩余 props
    for 名称,源 in (源们 or {}).items():#逐普通源
        绑定[标准钩子属性名(名称)]=可观察钩子(源)#普通钩子座位
    for 名称,源 in (键控源 or {}).items():#逐键控源
        绑定[标准钩子属性名(名称)]=键控可观察钩子(源)#键控钩子座位
    return 绑定#返回

def 跑注入(条目,绑定,动作):#跑 inject
    """声明派生的位置参数。"""
    注入=取字段(条目,'inject')#工厂
    if not 注入:#无工厂
        return 空注入属性#空
    参数=[]#位置参数
    if 绑定 is not None:#有绑定
        参数.append(取字段(绑定,'key'))#会话键
    if 动作 is not None:#有 actions
        参数.append(动作)#store actions
    return 绑定注入源(注入(*参数))#绑定源

def 缓存槽注入(面):#缓存调度 inject
    """按稳定对象身份规范化。"""
    if 面 is None:#无面
        return 空槽注入#空
    键=id(面)#缓存键
    已=槽注入缓存.get(键)#读缓存
    if 已 is not None:#命中
        return 已#返回
    定义=面.get('hooks') if isinstance(面,dict) else None#钩子定义
    if 定义 is None:#无 hooks
        已={'props':面 if isinstance(面,dict) else {}}#整面当 props
        槽注入缓存[键]=已#写入
        return 已#返回
    属性={键:值 for 键,值 in 面.items() if 键!='hooks'}#剩余
    工厂们=None#延迟工厂表
    for 名称,定义项 in 定义.items():#逐定义
        钩名=标准钩子属性名(名称)#标准名
        if callable(定义项):#延迟工厂
            工厂们=工厂们 or {}#懒建表
            工厂们[名称]=定义项#延迟工厂
        else:#可观察源
            属性[钩名]=可观察钩子(定义项)#绑钩子
    已={'props':属性} if 工厂们 is None else {'props':属性,'slotHookFactories':工厂们}#含工厂
    槽注入缓存[键]=已#写入
    return 已#返回

def 缓存根注入(条目,动作):#根 inject 缓存
    """按条目缓存。"""
    键=id(条目)#缓存键
    属性=根注入缓存.get(键)#读缓存
    if 属性 is None:#未命中
        属性=跑注入(条目,None,动作)#跑 inject
        根注入缓存[键]=属性#写入
    return 属性#返回

def 缓存会话注入(条目,绑定,动作):#会话 inject
    """按（条目 × 绑定）缓存。"""
    外=会话注入缓存.setdefault(id(条目),{})#按条目
    内键=id(绑定)#按绑定
    属性=外.get(内键)#读
    if 属性 is None:#未命中
        属性=跑注入(条目,绑定,动作)#跑 inject
        外[内键]=属性#写入
    return 属性#返回

def 缓存可选会话注入(条目,绑定,动作):#可选会话 inject
    """按（条目 × 绑定）缓存。"""
    外=可选会话注入缓存.setdefault(id(条目),{})#按条目
    内键=id(绑定)#按绑定
    属性=外.get(内键)#读
    if 属性 is None:#未命中
        属性=跑注入(条目,绑定,动作)#跑 inject
        外[内键]=属性#写入
    return 属性#返回

def 文案座位(面,命名空间):#合成 t 座位
    """按（面, 命名空间, 修订）缓存。"""
    按面=文案座位缓存.setdefault(id(面),{})#按面
    修订=取字段(面.getSnapshot() if hasattr(面,'getSnapshot') else 面['getSnapshot'](),'revision')#当前修订
    缓存=按面.get(命名空间)#按命名空间
    if 缓存 and 缓存['revision']==修订:#同修订
        return 缓存['t']#复用
    绑定=面.bind(命名空间) if hasattr(面,'bind') else 面['bind'](命名空间)#绑定命名空间
    def 翻译(键,参数=None):#包装翻译
        """每修订新包装。"""
        return 绑定(键,参数)#调用
    按面[命名空间]={'revision':修订,'t':翻译}#写入缓存
    return 翻译#返回

def 文案订阅(面):#订 locale
    """逐面 subscribe/getSnapshot 闭包对。"""
    键=id(面)#缓存键
    缓存=文案订阅缓存.get(键)#读缓存
    if 缓存 is None:#未建
        缓存={#闭包对
            'subscribe':lambda 回调:面.subscribe(回调) if hasattr(面,'subscribe') else 面['subscribe'](回调),#订阅面
            'getRevision':lambda:取字段(面.getSnapshot() if hasattr(面,'getSnapshot') else 面['getSnapshot'](),'revision'),#读修订
        }#对结束
        文案订阅缓存[键]=缓存#写入
    return 缓存#返回

def 用文案修订(面):#订 locale 修订
    """未安装时为 0。"""
    if 面 is None:#无面
        return 0#版本 0
    return 文案订阅(面)['getRevision']()#读修订

def 条目键于(条目):#取条目 key
    """按条目身份稳定。"""
    global 下一条目键#序号
    键=条目键表.get(id(条目))#读缓存
    if 键 is None:#未分配
        键=下一条目键#递增
        下一条目键+=1#加一
        条目键表[id(条目)]=键#写入
    return 键#返回

class 槽错误边界:#条目错误边界
    """组装错误穿透；其它失败显示崩溃面。"""

    def __init__(自身,槽键,条目错误时,子树=None):#构造
        """记下槽键与回调。"""
        自身.slotKey=槽键#槽键
        自身.onEntryError=条目错误时#崩溃回调
        自身.子树=子树#子节点
        自身.失败=False#初始未失败

    def 渲染(自身):#渲染
        """失败则崩溃面。"""
        if 自身.失败:#已失败
            return {'type':'slot-error','slotKey':自身.slotKey}#崩溃面
        try:#尝试子树
            return 自身.子树() if callable(自身.子树) else 自身.子树#正常子树
        except 槽组装错误:#组装错误穿透
            raise#再抛
        except Exception as 错误:#登记方崩溃
            print(f"slot entry crashed in '{自身.slotKey}':",错误)#打印
            自身.失败=True#标记失败
            自身.onEntryError(错误)#上报
            return {'type':'slot-error','slotKey':自身.slotKey}#崩溃面

def 物化标准绑定(绑定,可选):#物化标准
    """把一个绑定物化为稳定的框架钩子与普通 prop 座位。"""
    标准=dict(取字段(绑定,'props') or {})#拷贝 prop
    for 名称,源 in (取字段(绑定,'hooks') or {}).items():#逐钩子
        if 源 is None and not 可选:#严格缺源
            raise 槽组装错误(f"strict standard hook '{名称}' has no source")#抛错
        标准[标准钩子属性名(名称)]=可缺席可观察钩子(源) if 可选 else 可观察钩子(源)#钩子
    for 名称,源 in (取字段(绑定,'keyedHooks') or {}).items():#逐键控
        if 源 is None and not 可选:#严格缺源
            raise 槽组装错误(f"strict keyed standard hook '{名称}' has no source resolver")#抛错
        标准[标准钩子属性名(名称)]=键控可观察钩子(源)#键控钩子
    return 标准#返回

def 标准属性(作用域,根绑定,作用域绑定):#标准 props
    """上下文钩子工厂使用的稳定官方 props 对象。"""
    根=根标准缓存.get(id(根绑定))#根缓存
    if 根 is None:#未命中
        根=物化标准绑定(根绑定,False)#物化根
        根标准缓存[id(根绑定)]=根#写入
    if 作用域=='root':#仅根
        return 根#返回
    if 作用域绑定 is None:#缺绑定
        raise 槽组装错误(f"scope '{作用域}' rendered without a standard-source binding")#抛错
    缓存轴=会话标准缓存 if 作用域=='session' else 可选标准缓存#选缓存轴
    按根=缓存轴.setdefault(id(根绑定),{})#按根
    标准=按根.get(id(作用域绑定))#按作用域
    if 标准 is not None:#命中
        return 标准#返回
    标准={**根,**物化标准绑定(作用域绑定,作用域=='session-maybe')}#合并
    按根[id(作用域绑定)]=标准#写入
    return 标准#返回

def 作用域区域提供者(适配器):#区域提供者
    """把域自有作用域区域渲染器绑到当前作用域绑定。"""
    键=id(适配器)#缓存键
    提供者=作用域区域缓存.get(键)#读缓存
    if 提供者 is not None:#命中
        return 提供者#返回
    渲区=取字段(适配器,'renderArea')#渲染器
    if 渲区 is None:#无
        raise 槽组装错误("scope 'session' adapter does not provide its area renderer")#抛错
    def 区域提供者组件(属性):#提供者组件
        """当前绑定 + props。"""
        return 渲区(用作用域绑定(),属性)#渲染
    作用域区域缓存[键]=区域提供者组件#写入
    return 区域提供者组件#返回

def 标准工具包(宿主,条目,作用域,根绑定,作用域绑定):#合成工具包
    """标准座位 + locale/store/renderSlot/SessionProvider。"""
    标准=标准属性(作用域,根绑定,作用域绑定)#标准座位
    包=dict(标准)#工具包起点
    文案名=取字段(条目,'locale')#声明了文案
    if 文案名 is not None:#有
        面=宿主['locale']() if callable(宿主.get('locale') if isinstance(宿主,dict) else None) else (宿主['locale'] if isinstance(宿主,dict) else getattr(宿主,'locale',None))#locale 面
        if callable(面) and not hasattr(面,'bind'):#活 getter 误调
            面=面()#再取
        if 面 is None:#未安装
            raise 槽组装错误(f"entry declares locale namespace '{文案名}' but no locale face is installed (locale plugin missing from the composition?)")#抛错
        包['t']=文案座位(面,文案名)#t 座位
    作用域键=取字段(作用域绑定,'key') if 作用域绑定 is not None else None#键
    作用域存储绑定=作用域绑定 if 作用域键 is not None else None#有键可解析
    取存储=宿主['storeOf'] if isinstance(宿主,dict) else 宿主.storeOf#解析 store
    存储=取存储(条目,作用域存储绑定)#解析
    动作=None#actions
    if 存储 is not None:#有 store
        包['useStore']=可观察钩子(存储)#useStore 座位
        动作=取字段(存储,'actions')#actions
        包['actions']=动作#actions 座位
    子们=取字段(条目,'children')#有子声明
    if 子们 is not None:#有
        包['renderSlot']=绑定渲染槽(宿主,条目)#renderSlot 座位
        if any(取字段(规格,'kind')=='chain' for 规格 in (子们.values() if isinstance(子们,dict) else [])):#含链
            包['renderSlotChain']=绑定渲染槽链(宿主,条目)#链座位
        if any(取字段(规格,'scope')=='session' for 规格 in (子们.values() if isinstance(子们,dict) else [])):#含会话子
            取作用域=宿主['scope'] if isinstance(宿主,dict) else 宿主.scope#取适配器
            适配器=取作用域('session')#取适配器
            if 适配器 is None:#未安装
                raise 槽组装错误("entry declares a session child without an installed 'session' scope adapter")#抛错
            包['SessionProvider']=作用域区域提供者(适配器)#SessionProvider 座位
    return {'kit':包,'standard':标准,'actions':动作}#返回三件套

def 绑定槽钩子工厂(工厂们,标准,钩子上下文):#绑定延迟槽级工厂
    """为一个稳定的 renderSlot 出现点绑定。"""
    钩子={}#结果表
    for 名称,工厂 in 工厂们.items():#逐工厂
        钩子[标准钩子属性名(名称)]=工厂(标准,钩子上下文)#调用工厂
    return 钩子#返回

def 渲染条目(槽键,组件,包,标准,注入,槽注入,拥有方,钩子上下文,有钩子上下文):#渲染条目
    """无延迟工厂则直接展开；否则经上下文条目。"""
    工厂们=槽注入.get('slotHookFactories') if isinstance(槽注入,dict) else None#延迟工厂
    合并={**包,**注入,**(槽注入.get('props') if isinstance(槽注入,dict) else {}),**拥有方}#展开
    if 工厂们 is None:#无延迟工厂
        return 组件(合并) if callable(组件) else {'type':'entry','component':组件,'props':合并}#直接展开
    if not 有钩子上下文:#缺上下文
        raise 槽组装错误(f"slot '{槽键}' has contextual injected Hooks but no hookContext")#抛错
    上下文钩=绑定槽钩子工厂(工厂们,标准,钩子上下文)#绑工厂
    合并={**合并,**上下文钩}#再合
    return 组件(合并) if callable(组件) else {'type':'entry','component':组件,'props':合并}#展开

def 渲染条目体(宿主,条目,作用域,绑定,槽键,槽注入,拥有方,钩子上下文,有钩子上下文):#条目体
    """根/会话/可选会话共用。"""
    根绑定=用根绑定()#根绑定
    组件=取字段(条目,'component')#组件
    三件=标准工具包(宿主,条目,作用域,根绑定,绑定)#工具包
    if 作用域=='root':#根
        注入=缓存根注入(条目,三件['actions'])#根 inject
    elif 作用域=='session':#严格会话
        注入=缓存会话注入(条目,绑定,三件['actions'])#会话 inject
    else:#可选会话
        注入=缓存可选会话注入(条目,绑定,三件['actions'])#可选 inject
    return 渲染条目(槽键,组件,三件['kit'],三件['standard'],注入,槽注入,拥有方,钩子上下文,有钩子上下文)#渲染

class 可选会话条目:#可选会话化身
    """收养——唯一行为；身份在 undefined → 首个 id 上保持。"""

    def __init__(自身,条目,拥有方,槽键,槽注入,钩子上下文,有钩子上下文):#构造
        """记下 props 与化身记账。"""
        自身.entry=条目#条目
        自身.ownerProps=拥有方#拥有方
        自身.slotKey=槽键#槽键
        自身.slotInjected=槽注入#inject
        自身.hookContext=钩子上下文#上下文
        自身.hasHookContext=有钩子上下文#门闩
        自身.state=dict(首化身)#化身记账

    def 渲染(自身):#渲染
        """按 epoch 重挂体。"""
        宿主=用宿主()#宿主
        绑定=用作用域绑定()#当前绑定
        收养=自身.state['adopted']#已收养
        代数=自身.state['epoch']#化身代数
        键=取字段(绑定,'key')#当前键
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

def 渲染链结果(槽键,当选,选项):#链结果
    """同时保留覆盖层回退的树位置。"""
    回退=取字段(选项,'fallback') if 选项 else None#回退
    if not 取字段(选项,'overlay') if 选项 else False:#无覆盖层
        return 当选 if 当选 is not None else 回退#无覆盖层
    return {#覆盖层布局
        'type':'chain-overlay',#类型
        'slotKey':槽键,#槽键
        'fallbackVisible':当选 is None,#有当选则隐藏回退
        'fallback':回退,#回退内容
        'elected':当选,#当选
    }#树结束

def 渲染出口内容(宿主,槽键,拥有方,选项,作用域绑定):#出口内容
    """锚点后的 kind 调度。"""
    取规格=宿主['specOf'] if isinstance(宿主,dict) else 宿主.specOf#槽规范
    规格=取规格(槽键)#规范
    if not 规格:#未声明
        return None#空
    if 取字段(规格,'kind')=='chain' and 取字段(选项,'fallbackOnly') is True:#仅回退
        return 渲染链结果(槽键,None,选项)#仅回退模式
    if 取字段(规格,'scope')=='session' and 取字段(作用域绑定,'key') is None:#严格会话无键
        raise 槽组装错误(f"strict session slot '{槽键}' rendered without a scope binding")#抛错
    取条目=宿主['entriesOf'] if isinstance(宿主,dict) else 宿主.entriesOf#全部条目
    条目们=取条目(槽键)#条目
    槽注入=缓存槽注入(取字段(规格,'inject'))#调度 inject
    取胜出=宿主['entriesOfSlot'] if isinstance(宿主,dict) else 宿主.entriesOfSlot#胜出
    报告=宿主['reportEntryError'] if isinstance(宿主,dict) else 宿主.reportEntryError#报告

    def 守卫(条目,键=None,拥有=None):#带边界渲染
        """遮蔽 kind 崩溃时退位；链报告但不退位。"""
        拥有方值=拥有 if 拥有 is not None else 拥有方#拥有方
        有钩=选项 is not None and 'hookContext' in (选项 if isinstance(选项,dict) else {})#是否带上下文
        钩上下文=取字段(选项,'hookContext') if 选项 else None#钩子上下文
        def 条目错误时(错误):#崩溃回调
            """报告。"""
            报告(槽键,条目,错误,{'abdicate':取字段(规格,'kind')!='chain'})#报告
        作用域=取字段(规格,'scope')#作用域
        if 作用域=='session':#严格会话
            绑定=用作用域绑定()#当前绑定
            if 取字段(绑定,'key') is None:#无会话
                raise 槽组装错误(f"strict session slot '{槽键}' rendered without a scope binding")#抛错
            边界=槽错误边界(槽键,条目错误时,lambda:渲染条目体(用宿主(),条目,'session',绑定,槽键,槽注入,拥有方值,钩上下文,有钩))#边界
            return {'type':'strict-session-entry','key':取字段(绑定,'key'),'body':边界.渲染()}#树
        if 作用域=='session-maybe':#可选会话
            边界=槽错误边界(槽键,条目错误时,lambda:可选会话条目(条目,拥有方值,槽键,槽注入,钩上下文,有钩).渲染())#边界
            return {'type':'session-maybe-wrap','key':键,'body':边界.渲染()}#树
        边界=槽错误边界(槽键,条目错误时,lambda:渲染条目体(用宿主(),条目,'root',None,槽键,槽注入,拥有方值,钩上下文,有钩))#根边界
        return {'type':'root-entry','key':键,'body':边界.渲染()}#树

    def 干涸格():#干涸崩溃面
        """每个登记都已退位的格子。"""
        return {'type':'slot-error','slotKey':槽键}#崩溃面

    种类=取字段(规格,'kind')#种类
    if 种类=='single':#单条目
        胜出们=取胜出(槽键)#胜出者
        条目=胜出们[0] if 胜出们 else None#胜出
        if 条目 is None:#无胜出
            return 干涸格() if len(条目们)>0 else 取字段(选项,'fallback')#干涸或回退
        return 守卫(条目,条目键于(条目))#渲染胜出
    if 种类=='keyed':#键控
        条目键=取字段(选项,'entryKey')#请求键
        胜出们=取胜出(槽键)#胜出
        条目=next((项 for 项 in 胜出们 if 取字段(取字段(项,'options'),'key')==条目键),None)#按键找
        if 条目 is None:#未命中
            占用=any(取字段(取字段(项,'options'),'key')==条目键 for 项 in 条目们)#格是否曾占用
            return 干涸格() if 占用 else 取字段(选项,'fallback')#干涸或回退
        return 守卫(条目,条目键于(条目))#渲染
    if 种类=='chain':#链选举
        当选=None#当选节点
        for 条目 in 条目们:#逐条选举
            try:#跑选择器
                选择=取字段(条目,'select')#选择器
                命中=选择(拥有方) if callable(选择) else None#纯选择
            except Exception as 错误:#选择器抛错
                print(f"chain selector crashed in '{槽键}' ({取字段(条目,'registrant') or 'unknown registrant'}), treating as declined:",错误)#打印并谢绝
                continue#下一条
            if 命中 is not None:#命中
                当选=守卫(条目,条目键于(条目),{**拥有方,'matched':命中})#带 matched 渲染
                break#停止选举
        return 渲染链结果(槽键,当选,选项)#链结果
    胜出们=取胜出(槽键)#胜出行
    行们=[{'entry':条目,'id':取字段(取字段(条目,'options'),'id'),'order':取字段(取字段(条目,'options'),'order',0)} for 条目 in 胜出们]#活行
    行标识=set(项['id'] for 项 in 行们)#已有 id
    for 条目 in 条目们:#补干涸格
        标识=取字段(取字段(条目,'options'),'id')#id
        if 标识 in 行标识:#已有
            continue#跳过
        行标识.add(标识)#登记
        行们.append({'entry':None,'id':标识,'order':取字段(取字段(条目,'options'),'order',0)})#干涸行
    列表=sorted(行们,key=lambda 项:项['order'])#按 order 排
    仅=取字段(选项,'only') if 选项 else None#可选 id 过滤
    if 仅 is not None:#过滤
        列表=[项 for 项 in 列表 if 项['id']==仅]#过滤
    if len(列表)==0:#空列表
        return 取字段(选项,'fallback')#回退
    return {#列表片段
        'type':'slot-list',#类型
        'items':[#行
            守卫(项['entry'],f"e{条目键于(项['entry'])}") if 项['entry'] is not None else {'type':'slot-error','slotKey':槽键,'key':f"x{项['id']}"}#胜出或干涸
            for 项 in 列表
        ],#行结束
    }#树结束

class 槽出口:#槽出口
    """每个槽渲染点暴露稳定的 data-slot 包装。"""

    def __init__(自身,槽键,拥有方,选项=None):#构造
        """记下键与 props。"""
        自身.slotKey=槽键#槽键
        自身.ownerProps=拥有方#拥有方
        自身.opts=选项#渲染选项

    def 渲染(自身):#渲染
        """锚点包装 + 调度内容。"""
        宿主=用宿主()#宿主
        订=宿主['subscribe'] if isinstance(宿主,dict) else 宿主.subscribe#订变更
        取版本=宿主['getVersion'] if isinstance(宿主,dict) else 宿主.getVersion#读版本
        订(自身.slotKey,lambda:None)#订变更（驱动重读）
        取版本(自身.slotKey)#读版本
        面=宿主['locale'] if isinstance(宿主,dict) else getattr(宿主,'locale',None)#locale
        if callable(面) and not hasattr(面,'bind'):#活 getter
            面=面()#再取
        用文案修订(面)#订 locale
        作用域绑定=用作用域绑定()#作用域绑定
        return {#锚点包装
            'type':'slot-outlet',#类型
            'slotKey':自身.slotKey,#锚点
            'style':锚点样式,#样式
            'content':渲染出口内容(宿主,自身.slotKey,自身.ownerProps,自身.opts,作用域绑定),#调度内容
        }#树结束

class 根出口:#根出口
    """外壳唯一的 ctx 级渲染入口。"""

    def __init__(自身,拥有方):#构造
        """记下拥有方。"""
        自身.ownerProps=拥有方#拥有方

    def 渲染(自身):#渲染
        """未登记的 root 是启动顺序失败。"""
        宿主=用宿主()#宿主
        订=宿主['subscribe'] if isinstance(宿主,dict) else 宿主.subscribe#订 root
        取版本=宿主['getVersion'] if isinstance(宿主,dict) else 宿主.getVersion#root 版本
        订('root',lambda:None)#订
        取版本('root')#版本
        面=宿主['locale'] if isinstance(宿主,dict) else getattr(宿主,'locale',None)#locale
        if callable(面) and not hasattr(面,'bind'):#活 getter
            面=面()#再取
        用文案修订(面)#订 locale
        取胜出=宿主['entriesOfSlot'] if isinstance(宿主,dict) else 宿主.entriesOfSlot#胜出
        取条目=宿主['entriesOf'] if isinstance(宿主,dict) else 宿主.entriesOf#全部
        报告=宿主['reportEntryError'] if isinstance(宿主,dict) else 宿主.reportEntryError#报告
        胜出们=取胜出('root')#根胜出
        条目=胜出们[0] if 胜出们 else None#胜出
        if 条目 is None:#无胜出
            if len(取条目('root'))>0:#有登记但全部退位
                return {'type':'slot-error','slotKey':'root'}#干涸崩溃
            raise 槽组装错误("renderSlot('root') before any 'root' registration (boot order)")#启动顺序
        def 条目错误时(错误):#崩溃退位
            """报告。"""
            报告('root',条目,错误,{'abdicate':True})#退位
        边界=槽错误边界('root',条目错误时,lambda:渲染条目体(宿主,条目,'root',None,'root',空槽注入,自身.ownerProps,None,False))#根边界
        return {#根锚点
            'type':'root-outlet',#类型
            'slotKey':'root',#根锚点
            'style':锚点样式,#样式
            'key':条目键于(条目),#条目 key
            'body':边界.渲染(),#体
        }#树结束

def 创建槽渲染器():#工厂
    """构建安装进 SlotRegistry 的渲染器。"""
    def 渲染根(宿主,拥有方):#渲染根
        """提供者树。"""
        宿主栈.append(宿主)#压宿主
        try:#渲
            def 子树():#可选会话包根出口
                """ScopeProvider session-maybe。"""
                return 作用域提供者('session-maybe',lambda:根出口(拥有方).渲染()).渲染()#可选会话
            return {#提供者树
                'type':'slot-renderer-root',#类型
                'tree':根标准提供者(子树).渲染(),#根源
            }#树结束
        finally:#出栈
            宿主栈.pop()#出栈
    return {'renderRoot':渲染根}#渲染器

createSlotRenderer=创建槽渲染器#上游名
SlotOutlet=槽出口#上游名
RootOutlet=根出口#上游名
SlotErrorBoundary=槽错误边界#上游名
