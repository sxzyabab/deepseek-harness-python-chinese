import weakref,threading
from concurrent.futures import Future as _原生Future
from ...依赖 import cordis
上下文=cordis.上下文
from .存储 import 具名条目,匿名条目,作用域层集

class 作用域错误(Exception):
    """内核作用域包的异常基类。"""

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._未来=_原生Future()

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():
            自身._未来.set_result(值)
        return 值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():
            if isinstance(错误,BaseException):
                自身._未来.set_exception(错误)
            else:
                包装=作用域错误('任务被拒绝')
                包装.原因=错误
                自身._未来.set_exception(包装)

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)

__all__=(
    '弱身份表',
    '作用域父绑定',
    '作用域',
    '绑定作用域父','获取作用域父','获取作用域链',
    '创建作用域','获取作用域',
    '作用域目标','是否作用域载体','获取载体键',
    '具名条目','匿名条目','作用域层集',
)

作用域符号=object()#写入 ctx.扩展 的作用域标签键，相当于 JS Symbol('dsh.scope')

class 弱身份表:
    """按对象身份存取，键可被回收，对应 JS WeakMap。键死则条目清掉，标识复用不会误命中。"""
    def __init__(自身):
        """建立空表。"""
        自身._表={}

    def 设(自身,键,值):
        """按身份写入；键被回收时自动摘掉本条。"""
        标识=id(键)#对象标识（仅作槽位，命中仍靠 is）
        def 清理(引用):
            """键被回收时摘掉条目；仅当槽里仍是本条弱引用才删，避免竞态误删。"""
            当前=自身._表.get(标识)
            if 当前 is not None and 当前[0] is 引用:
                自身._表.pop(标识,None)
        自身._表[标识]=(weakref.ref(键,清理),值)

    def 取(自身,键):
        """按身份读取，缺失或键已死/标识复用为 None。"""
        项=自身._表.get(id(键))
        if 项 is None:
            return None
        引用,值=项
        if 引用() is 键:
            return 值
        return None

    def 有(自身,键):
        """是否仍登记着该活键。"""
        项=自身._表.get(id(键))
        if 项 is None:
            return False
        return 项[0]() is 键

载体键表=弱身份表()#载体 → 路由键；has 用来区分无键载体与非载体
作用域父表=弱身份表()#键 → 包围父键；登记向下继承、事件向上放行共用此链

class 作用域载体:
    """仅用于路由的事件接收器；不暴露主体属性，真实主体在事件载荷里。"""
    pass#故意空类，过滤挂在实例 __dict__

class 作用域父绑定:
    """移动一个作用域键父链接的特权句柄。仅原绑定者持有；空白会话重组约定由持有者遵守。"""
    def __init__(自身,键):
        """记下被绑定的键。"""
        自身._键=键

    def 改接(自身,父):
        """把绑定键改接到另一个父，循环检查与首次绑定相同。"""
        链接作用域父(自身._键,父)

class 作用域:
    """已铸造的注册作用域及其静止拆除边界。"""
    def __init__(自身,上下文,原始拆除,拆除):
        """保存上下文与拆除边界。"""
        自身.上下文=上下文
        自身.原始拆除=原始拆除#精确 Cordis disposer，嵌进有序组合 effect 时用
        自身.拆除=拆除#共用幂等完全停稳边界；竞态调用等待同一次 teardown

def 链接作用域父(键,父):
    """绑定与每次改接共享的、带循环检查的写入。成环则拒绝，因为每个链消费方都走到根。"""
    游标=父
    while 游标 is not None:
        if 游标 is 键:
            raise 作用域错误('dsh-scope：作用域父链接会成环')#包名不译
        游标=作用域父表.取(游标)
    作用域父表.设(键,父)

def 绑定作用域父(键,父):
    """把父绑定为键的包围作用域，只绑一次，返回唯一可改接该键的绑定。

    已有父的键会抛错：没有开放的改接路径，因此除原绑定者外谁都不能移动作用域祖先。
    """
    if 作用域父表.有(键):
        raise 作用域错误('dsh-scope：作用域键已绑定父级；改接须用原绑定返回的句柄')#包名不译
    链接作用域父(键,父)
    return 作用域父绑定(键)

def 获取作用域父(键):
    """读一个键的包围作用域，根作用域为 None。"""
    return 作用域父表.取(键)

def 获取作用域链(键):
    """从某键到其根祖先的链，最近者在前；键为 None 时为空链。"""
    链=[]
    游标=键
    while 游标 is not None:
        链.append(游标)
        游标=作用域父表.取(游标)
    return 链

def 等到纤程静止(纤程对象):
    """即使原始拆除器已被领取，也跟随 Cordis 纤程走完拆除与 inertia。"""
    纤程对象.dispose().等待()
    while 纤程对象.inertia is not None:
        纤程对象.inertia.等待()

def 空插件(上下文,配置=None):
    """作为支撑作用域纤程的共享空操作插件；纤程只为拥有经作用域上下文做出的注册。"""
    return

def 创建作用域(上下文,键,选项=None):
    """在上下文下铸造一个作用域，返回作用域上下文以及精确/共享拆除边界。

    作用域上下文继承铸造插件的依赖 API，并拥有经它做出的每一项注册。
    """
    if 选项 is not None and '父' in 选项:
        绑定作用域父(键,选项['父'])
    纤程对象=上下文.启动插件(空插件)
    带标签=纤程对象.ctx.扩展({作用域符号:键})
    拆除中=None
    def 拆除():
        """竞态共用一次静止拆除。"""
        nonlocal 拆除中
        if 拆除中 is None:
            任务=操作任务()
            拆除中=任务
            try:
                等到纤程静止(纤程对象)
                任务.兑现(None)
            except Exception as 错误:
                任务.拒绝(错误)
                raise
        拆除中.等待()
    return 作用域(带标签,纤程对象.dispose,拆除)

def 获取作用域(上下文):
    """读上下文继承的最近作用域标签，无作用域上下文为 None。"""
    return 上下文.__dict__.get(作用域符号)

def 作用域目标(基,键):
    """构建一个不透明接收器：保留基过滤器，无标签监听器全局准入，带标签监听器在匹配键或其任一祖先时准入。

    包围作用域拥有的监听器收到每个后代作用域的事件；派发键之下的标签仍排除——事件沿链向上流，从不向下。
    """
    基过滤器=None
    来自类型=False
    if hasattr(基,'__dict__') and 上下文.过滤 in 基.__dict__:
        基过滤器=基.__dict__[上下文.过滤]
    else:#沿类型链，对齐 TS 的 obj[Context.filter]
        for 类 in type(基).__mro__:
            if 上下文.过滤 in 类.__dict__:
                基过滤器=类.__dict__[上下文.过滤]
                来自类型=True
                break
    载体=作用域载体()
    def 过滤器(监听上下文):
        """作用域过滤器：先基过滤，再按标签沿派发键向上匹配。"""
        if 基过滤器 is not None:
            if 来自类型:#类型方法对应 filter.call(base, ctx)
                if not 基过滤器(基,监听上下文):
                    return False
            else:
                if not 基过滤器(监听上下文):
                    return False
        标签=获取作用域(监听上下文)
        if 标签 is None:
            return True
        游标=键
        while 游标 is not None:
            if 游标 is 标签:
                return True
            游标=作用域父表.取(游标)
        return False
    载体.__dict__[上下文.过滤]=过滤器
    载体键表.设(载体,键)
    return 载体

def 是否作用域载体(值):
    """测试某值是否为作用域载体。"""
    if 值 is None or isinstance(值,(str,bytes,int,float,bool)):
        return False
    return 载体键表.有(值)

def 获取载体键(值):
    """读载体的路由键；无键或非载体值为 None。"""
    if not 是否作用域载体(值):
        return None
    return 载体键表.取(值)
