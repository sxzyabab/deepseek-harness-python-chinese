"""渲染器宿主与标准源作用域的内部绑定。

对齐上游 `ui-renderer/src/client/bindings.tsx`。公开面仅中文名。
无真 React Context：用显式栈模拟提供者。
宿主为 槽宿主面 对象；可观察源与作用域适配器为 dict。
"""
from .绑定选择器 import 绑定快照选择器#uSES 绑定

__all__=[#仅中文公开名
    '槽组装错误','宿主上下文','用宿主','根绑定上下文','作用域绑定上下文',
    '用根绑定','用作用域绑定','可观察钩子','可缺席可观察钩子','键控可观察钩子',
    '根标准提供者','作用域提供者','缺席源','恒等','可观察源',
]#公开面结束

class 槽组装错误(Exception):
    """缺少渲染器组装依赖。边界会再抛。"""
    pass#无额外字段

class 可观察源:
    """subscribe/getSnapshot 对象。对齐 uSES 裸源。"""
    def __init__(自身,取快照,订阅):
        """记下闭包。"""
        自身.getSnapshot=取快照#读快照
        自身.subscribe=订阅#订阅

宿主栈=[]#宿主 API 栈
根绑定栈=[]#根标准源栈
作用域绑定栈=[]#作用域标准源栈

宿主上下文=宿主栈#栈即上下文
根绑定上下文=根绑定栈#栈即上下文
作用域绑定上下文=作用域绑定栈#栈即上下文

def 取缺席快照():
    """缺席源快照恒 None。"""
    return None#缺席

def 空退订():
    """空订阅的退订器。"""
    return None#无

def 空订阅(回调):
    """缺席源订阅。"""
    return 空退订#退订

缺席源=可观察源(取缺席快照,空订阅)#缺席占位源

def 恒等(值):
    """默认选择器。"""
    return 值#原样

def 忽略快照(快照):
    """占位选择：丢快照。"""
    return None#缺席值

钩子缓存={}#源→钩子缓存（以 id 近似 WeakMap）
键控钩子缓存={}#键控缓存

def 用宿主():
    """缺宿主则抛组装错误。"""
    if len(宿主栈)==0:#缺
        raise 槽组装错误('slot machinery rendered outside the installed renderer tree')#缺宿主
    return 宿主栈[-1]#返回

def 用根绑定():
    """缺根则抛。"""
    if len(根绑定栈)==0:#缺
        raise 槽组装错误('slot rendered outside the root standard-source provider')#缺根
    return 根绑定栈[-1]#返回

def 用作用域绑定():
    """缺作用域则抛。"""
    if len(作用域绑定栈)==0:#缺
        raise 槽组装错误('scoped slot rendered outside its scope provider')#缺作用域
    return 作用域绑定栈[-1]#返回

def 可观察钩子(源):
    """按源缓存一次选择器钩子。源为对象。"""
    键=id(源)#近似 WeakMap 键
    钩子=钩子缓存[键] if 键 in 钩子缓存 else None#读缓存
    if 钩子 is None:#未缓存
        钩子=绑定快照选择器(源)#按源缓存一次
        钩子缓存[键]=钩子#写入
    return 钩子#返回

def 用缺席快照(选择器=None,相等=None):
    """仍走一次订阅，保持钩子序。"""
    可观察钩子(缺席源)(忽略快照)#占位订阅
    return None#缺席值

def 可缺席可观察钩子(源):
    """有源则绑定；缺席时返回 None 的选择器钩子。"""
    if 源 is not None:#有源
        return 可观察钩子(源)#绑定
    return 用缺席快照#仍走一次，保持钩子序

def 缺席键控钩子(开放键,选择器=None,相等=None):
    """走缺席源。"""
    选=恒等 if 选择器 is None else 选择器#选择器
    return 可观察钩子(缺席源)(选,相等)#缺席键控族

def 键控可观察钩子(源):
    """绑定开放键源族。"""
    if 源 is None:#缺席族
        return 缺席键控钩子#缺席
    键=id(源)#缓存键
    钩子=键控钩子缓存[键] if 键 in 键控钩子缓存 else None#读缓存
    if 钩子 is None:#未缓存
        def 按键选择(开放键,选择器=None,相等=None):
            """按键解析再绑定。源为 (键)→可观察源。"""
            解析=源(开放键)#解析
            用值=可观察钩子(解析 if 解析 is not None else 缺席源)#绑定
            选=恒等 if 选择器 is None else 选择器#选择器
            return 用值(选,相等)#调用选择器
        钩子=按键选择#写入形
        键控钩子缓存[键]=钩子#写入
    return 钩子#返回

class 根标准提供者:
    """让树订阅原子组装的根标准源名册。"""
    def __init__(自身,子树=None):
        """记下子树。"""
        自身.子树=子树#子节点

    def 渲染(自身):
        """提供根绑定。宿主为对象；root 源为 dict。"""
        宿主=用宿主()#宿主
        绑定=可观察钩子(宿主.root)(恒等)#根绑定身份选择
        根绑定栈.append(绑定)#压栈
        try:#渲子
            结果=自身.子树()#子树为 thunk
        finally:#出栈
            根绑定栈.pop()#出栈
        return {'type':'root-standard-provider','binding':绑定,'children':结果}#树

class 作用域提供者:
    """先订阅作用域名册，再解析并绑定其当前适配器。"""
    def __init__(自身,作用域,子树=None):
        """作用域为 session 或 session-maybe。"""
        自身.scope=作用域#作用域名
        自身.子树=子树#子节点

    def 渲染(自身):
        """提供作用域绑定。适配器为 dict。"""
        宿主=用宿主()#宿主
        可观察钩子(宿主.scopeRevision)(恒等)#适配器名册版本
        适配器=宿主.scope(自身.scope)#取适配器
        if 适配器 is None:#未安装
            raise 槽组装错误("scope '"+自身.scope+"' rendered without an installed adapter")#抛错
        当前=适配器['current']#当前源
        绑定=可观察钩子(当前)(恒等)#当前作用域绑定
        作用域绑定栈.append(绑定)#压栈
        try:#渲子
            结果=自身.子树()#子树为 thunk
        finally:#出栈
            作用域绑定栈.pop()#出栈
        return {'type':'scope-provider','scope':自身.scope,'binding':绑定,'children':结果}#树
