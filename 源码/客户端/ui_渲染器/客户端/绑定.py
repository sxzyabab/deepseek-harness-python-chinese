from .绑定选择器 import 绑定快照选择器#uSES 绑定
from ..异常 import 槽组装错误#本包异常

__all__=[#仅中文公开名
    '槽组装错误','宿主上下文','用宿主','根绑定上下文','作用域绑定上下文',
    '用根绑定','用作用域绑定','可观察钩子','可缺席可观察钩子','键控可观察钩子',
    '根标准提供者','作用域提供者','缺席源','恒等','可观察源',
]#公开面结束

class 可观察源:
    'subscribe/getSnapshot 对象。对齐 uSES 裸源'
    def __init__(自身,取快照,订阅):
        '记下闭包'
        自身.getSnapshot=取快照#读快照
        自身.subscribe=订阅#订阅

宿主栈=[]#宿主 API 栈
根绑定栈=[]#根标准源栈
作用域绑定栈=[]#作用域标准源栈

宿主上下文=宿主栈#栈即上下文
根绑定上下文=根绑定栈#栈即上下文
作用域绑定上下文=作用域绑定栈#栈即上下文

def 取缺席快照():
    '缺席源快照恒 None'
    return None#缺席

def 空退订():
    '空订阅的退订器'
    return None#无

def 空订阅(回调):
    '缺席源订阅'
    return 空退订#退订

缺席源=可观察源(取缺席快照,空订阅)#缺席占位源

def 恒等(值):
    '默认选择器'
    return 值#原样

def 忽略快照(快照):
    '占位选择：丢快照'
    return None#缺席值

钩子缓存={}#源→钩子缓存（以 id 近似 WeakMap）
键控钩子缓存={}#键控缓存

def 用宿主():
    '缺宿主则抛组装错误'
    if len(宿主栈)==0:#缺
        raise 槽组装错误('slot machinery rendered outside the installed renderer tree')#缺宿主
    return 宿主栈[-1]#返回

def 用根绑定():
    '缺根则抛'
    if len(根绑定栈)==0:#缺
        raise 槽组装错误('slot rendered outside the root standard-source provider')#缺根
    return 根绑定栈[-1]#返回

def 用作用域绑定():
    '缺作用域则抛'
    if len(作用域绑定栈)==0:#缺
        raise 槽组装错误('scoped slot rendered outside its scope provider')#缺作用域
    return 作用域绑定栈[-1]#返回

def 可观察钩子(源):
    '按源缓存一次选择器钩子。源为对象'
    键=id(源)#近似 WeakMap 键
    钩子=钩子缓存[键] if 键 in 钩子缓存 else None#读缓存
    if 钩子 is None:#未缓存
        钩子=绑定快照选择器(源)#按源缓存一次
        钩子缓存[键]=钩子#写入
    return 钩子#返回

def 用缺席快照(选择器=None,相等=None):
    '仍走一次订阅，保持钩子序'
    可观察钩子(缺席源)(忽略快照)#占位订阅
    return None#缺席值

def 可缺席可观察钩子(源):
    '有源则绑定；缺席时返回 None 的选择器钩子'
    if 源 is not None:#有源
        return 可观察钩子(源)#绑定
    return 用缺席快照#仍走一次，保持钩子序

无默认键=object()#没有默认键时的缓存哨兵

def 解析键控调用(默认键,开放键或选择器,第二,相等):
    '读 (键, 成员)、(键, 选择器, 相等) 或 (选择器, 相等)'
    if isinstance(开放键或选择器,str) is False:#第一参是选择器
        return {
            'key':默认键,#默认键
            'member':None,#没有成员
            'selector':开放键或选择器,#选择器
            'equal':第二,#相等
        }
    if isinstance(第二,str):#第二参是成员名
        return {
            'key':开放键或选择器,#开放键
            'member':第二,#成员
            'selector':None,#不经选择器
            'equal':None,#成员调用不带相等
        }
    return {
        'key':开放键或选择器,#开放键
        'member':None,#没有成员
        'selector':第二,#选择器
        'equal':相等,#相等
    }

def 缺席键控钩子(开放键或选择器,第二=None,相等=None):
    '源族缺席时仍解析调用形，结果走缺席源'
    调用=解析键控调用(None,开放键或选择器,第二,相等)#三种调用形
    选=恒等 if 调用['selector'] is None else 调用['selector']#成员调用用恒等
    return 可观察钩子(缺席源)(选,调用['equal'])#缺席快照

def 键控可观察钩子(源,默认键=None):
    '绑定开放键源族。第二参是字符串时作为成员交给源'
    if 源 is None:#缺席族
        return 缺席键控钩子#缺席钩子
    源键=id(源)#源身份
    按源=键控钩子缓存[源键] if 源键 in 键控钩子缓存 else None#按源的默认键表
    if 按源 is None:#未建
        按源={}#默认键→钩子
        键控钩子缓存[源键]=按源#写入
    缓存键=无默认键 if 默认键 is None else 默认键#区分未传默认键
    钩子=按源[缓存键] if 缓存键 in 按源 else None#读钩子
    if 钩子 is None:#未缓存
        def 按键选择(开放键或选择器,第二=None,相等=None):
            '解析键和成员后再绑定。成员要作为第二个参数传给源'
            调用=解析键控调用(默认键,开放键或选择器,第二,相等)#调用形
            if 调用['key'] is None:#没有键
                解析=None#缺席
            elif 调用['member'] is None:#只要整份源
                解析=源(调用['key'])#一个参数
            else:#成员源
                解析=源(调用['key'],调用['member'])#键和成员
            用值=可观察钩子(解析 if 解析 is not None else 缺席源)#绑定解析结果
            选=恒等 if 调用['selector'] is None else 调用['selector']#默认恒等
            return 用值(选,调用['equal'])#选出切片
        钩子=按键选择#按默认键缓存
        按源[缓存键]=钩子#写入
    return 钩子#返回

class 根标准提供者:
    '让树订阅原子组装的根标准源名册'
    def __init__(自身,子树=None):
        '记下子树'
        自身.子树=子树#子节点

    def 渲染(自身,保留=False):
        '提供根绑定。保留为真时栈留到根拆除'
        宿主=用宿主()#宿主
        绑定=可观察钩子(宿主.root)(恒等)#根绑定身份选择
        根绑定栈.append(绑定)#压栈
        try:#渲子
            结果=自身.子树()#子树为 thunk，返回节点
        except Exception:#失败先出栈
            根绑定栈.pop()#出栈
            raise#上抛
        if 保留 is False:#临时提供者
            根绑定栈.pop()#出栈
        return 结果#节点本身

class 作用域提供者:
    '先订阅作用域名册，再解析并绑定其当前适配器'
    def __init__(自身,作用域,子树=None):
        '作用域为 session 或 session-maybe'
        自身.scope=作用域#作用域名
        自身.子树=子树#子节点

    def 渲染(自身,保留=False):
        '提供作用域绑定。保留为真时栈留到根拆除'
        宿主=用宿主()#宿主
        可观察钩子(宿主.scopeRevision)(恒等)#适配器名册版本
        适配器=宿主.scope(自身.scope)#取适配器
        if 适配器 is None:#未安装
            raise 槽组装错误("scope '"+自身.scope+"' rendered without an installed adapter")#抛错
        if isinstance(适配器,dict):#字典适配器
            当前=适配器['current']#当前源
        else:#对象适配器
            当前=适配器.current#当前源
        绑定=可观察钩子(当前)(恒等)#当前作用域绑定
        作用域绑定栈.append(绑定)#压栈
        try:#渲子
            结果=自身.子树()#子树为 thunk，返回节点
        except Exception:#失败先出栈
            作用域绑定栈.pop()#出栈
            raise#上抛
        if 保留 is False:#临时提供者
            作用域绑定栈.pop()#出栈
        return 结果#节点本身
