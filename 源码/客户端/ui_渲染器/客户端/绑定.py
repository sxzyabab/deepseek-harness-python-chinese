"""渲染器宿主与标准源作用域的内部绑定。

对齐上游 `ui-renderer/src/client/bindings.tsx`。公开面仅中文名。
无真 React Context：用线程局部/显式栈模拟提供者。
"""
from .绑定选择器 import 绑定快照选择器#uSES 绑定

__all__=[#仅中文公开名
    '槽组装错误','宿主上下文','用宿主','根绑定上下文','作用域绑定上下文',
    '用根绑定','用作用域绑定','可观察钩子','可缺席可观察钩子','键控可观察钩子',
    '根标准提供者','作用域提供者','缺席源','恒等',
]#公开面结束

class 槽组装错误(Exception):#缺少渲染器组装依赖
    """边界会再抛。"""

宿主栈=[]#宿主 API 栈
根绑定栈=[]#根标准源栈
作用域绑定栈=[]#作用域标准源栈

宿主上下文=宿主栈#上游名别面
根绑定上下文=根绑定栈#上游名别面
作用域绑定上下文=作用域绑定栈#上游名别面

缺席源={#缺席占位源
    'getSnapshot':lambda:None,#恒 None
    'subscribe':lambda _回调:lambda:None,#空订阅
}#缺席源结束

恒等=lambda 值:值#默认选择器
钩子缓存={}#源→钩子缓存（以 id 近似 WeakMap）
键控钩子缓存={}#键控缓存

def 用宿主():#读宿主
    """缺宿主则抛组装错误。"""
    if not 宿主栈:#缺
        raise 槽组装错误('slot machinery rendered outside the installed renderer tree')#缺宿主
    return 宿主栈[-1]#返回

def 用根绑定():#读根绑定
    """缺根则抛。"""
    if not 根绑定栈:#缺
        raise 槽组装错误('slot rendered outside the root standard-source provider')#缺根
    return 根绑定栈[-1]#返回

def 用作用域绑定():#读作用域绑定
    """缺作用域则抛。"""
    if not 作用域绑定栈:#缺
        raise 槽组装错误('scoped slot rendered outside its scope provider')#缺作用域
    return 作用域绑定栈[-1]#返回

def 可观察钩子(源):#绑定钩子
    """按源缓存一次选择器钩子。"""
    键=id(源)#近似 WeakMap 键
    钩子=钩子缓存.get(键)#读缓存
    if 钩子 is None:#未缓存
        钩子=绑定快照选择器(源)#按源缓存一次
        钩子缓存[键]=钩子#写入
    return 钩子#返回

def 用缺席快照(_选择器,_相等=None):#恒 None
    """仍走一次订阅，保持钩子序。"""
    可观察钩子(缺席源)(lambda _快照:None)#占位订阅
    return None#缺席值

def 可缺席可观察钩子(源):#可缺席钩子
    """有源则绑定；缺席时返回 None 的选择器钩子。"""
    if 源 is not None:#有源
        return 可观察钩子(源)#绑定
    return 用缺席快照#仍走一次，保持钩子序

def 缺席键控钩子(_键,选择器=None,相等=None):#缺席键控族
    """走缺席源。"""
    return 可观察钩子(缺席源)(选择器 or 恒等,相等)#缺席键控族

def 键控可观察钩子(源):#键控钩子
    """绑定开放键源族。"""
    if 源 is None:#缺席族
        return 缺席键控钩子#缺席
    键=id(源)#缓存键
    钩子=键控钩子缓存.get(键)#读缓存
    if 钩子 is None:#未缓存
        def 按键选择(开放键,选择器=None,相等=None):#按键选择
            """按键解析再绑定。"""
            解析=源(开放键)#解析
            用值=可观察钩子(解析 if 解析 is not None else 缺席源)#绑定
            return 用值(选择器 or 恒等,相等)#调用选择器
        钩子=按键选择#写入形
        键控钩子缓存[键]=钩子#写入
    return 钩子#返回

class 根标准提供者:#根标准源提供者
    """让树订阅原子组装的根标准源名册。"""

    def __init__(自身,子树=None):#构造
        """记下子树。"""
        自身.子树=子树#子节点

    def 渲染(自身):#结构树
        """提供根绑定。"""
        宿主=用宿主()#宿主
        绑定=可观察钩子(宿主['root'] if isinstance(宿主,dict) else 宿主.root)(lambda 值:值)#根绑定身份选择
        根绑定栈.append(绑定)#压栈
        try:#渲子
            结果=自身.子树() if callable(自身.子树) else 自身.子树#子树
        finally:#出栈
            根绑定栈.pop()#出栈
        return {'type':'root-standard-provider','binding':绑定,'children':结果}#树

class 作用域提供者:#作用域提供者
    """先订阅作用域名册，再解析并绑定其当前适配器。"""

    def __init__(自身,作用域,子树=None):#构造
        """作用域为 session 或 session-maybe。"""
        自身.scope=作用域#作用域名
        自身.子树=子树#子节点

    def 渲染(自身):#结构树
        """提供作用域绑定。"""
        宿主=用宿主()#宿主
        修订源=宿主['scopeRevision'] if isinstance(宿主,dict) else 宿主.scopeRevision#版本源
        可观察钩子(修订源)(lambda 值:值)#适配器名册版本
        取作用域=宿主['scope'] if isinstance(宿主,dict) else 宿主.scope#取适配器
        适配器=取作用域(自身.scope)#取适配器
        if 适配器 is None:#未安装
            raise 槽组装错误(f"scope '{自身.scope}' rendered without an installed adapter")#抛错
        当前=适配器['current'] if isinstance(适配器,dict) else 适配器.current#当前源
        绑定=可观察钩子(当前)(lambda 值:值)#当前作用域绑定
        作用域绑定栈.append(绑定)#压栈
        try:#渲子
            结果=自身.子树() if callable(自身.子树) else 自身.子树#子树
        finally:#出栈
            作用域绑定栈.pop()#出栈
        return {'type':'scope-provider','scope':自身.scope,'binding':绑定,'children':结果}#树

HostContext=宿主上下文#上游名
RootStandardProvider=根标准提供者#上游名
ScopeProvider=作用域提供者#上游名
SlotAssemblyError=槽组装错误#上游名
useHost=用宿主#上游名
useRootBinding=用根绑定#上游名
useScopeBinding=用作用域绑定#上游名
observableHook=可观察钩子#上游名
maybeObservableHook=可缺席可观察钩子#上游名
keyedObservableHook=键控可观察钩子#上游名
