"""Session Controller 适配器：选择器钩子与 Slot 作用域数据。

对齐上游 `ui-session/src/client/index.ts`。公开面仅中文名。
TypeScript 声明合并面以注释保留；可执行面全量落中文。
"""
from ...store import 通知订阅者们#订阅者通知
from .会话提供方 import 渲染会话区域#SessionProvider 渲染语义

__all__=[#仅中文公开名
    '注入','应用','会话界面','待处理交互基座','标准钩子属性名',
    '内置源','相同待处理交互',
]#公开面结束

注入=['sessions','slots']#所需的 Controller 与渲染器服务

def 标准钩子属性名(名称):#钩子到标准 prop 名
    """`session` → `useSession`。"""
    if not 名称:#空
        return 'use'#仅前缀
    return 'use'+名称[0].upper()+名称[1:]#首字母大写加 use

class 待处理交互基座:#每个会话作用域待处理交互的公共身份
    """不透明请求身份；替换请求必须换新 key。"""

    def __init__(自身,键,种类,会话标识):#构造基座
        """记下 key/kind/sessionId。"""
        自身.key=键#请求键
        自身.kind=种类#展示种类
        自身.sessionId=会话标识#所属会话

class 待处理交互条目:#域内一条待处理记录
    """交互值与拆卸委托。"""

    def __init__(自身,交互,委托):#构造
        """记下值与委托。"""
        自身.interaction=交互#交互值
        自身.delegate=委托#拆卸委托

class 待处理交互域:#单一待处理域
    """按 key 索引；跨域优先级由 precedence 决定。"""

    def __init__(自身,优先级,已变更):#构造域
        """优先级函数越大胜出；变更时通知投影。"""
        自身.优先级=优先级#跨域优先级
        自身.已变更=已变更#变更通知
        自身.值表={}#按 key 索引

    def 值快照(自身):#当前域全部交互值
        """剥掉委托只留值。"""
        return [条目.interaction for 条目 in 自身.值表.values()]#值列表

    def 发布(自身,交互,委托):#发布并返回撤销
        """禁止同 key 重复。"""
        键=交互.key if hasattr(交互,'key') else 交互['key']#取键
        if 键 in 自身.值表:#重复
            raise Error(f"ui-session: duplicate pending interaction key '{键}'")#重复键
        自身.值表[键]=待处理交互条目(交互,委托)#写入
        自身.已变更()#通知投影
        活跃=[True]#撤销幂等门闩

        def 撤销():#撤销函数
            """已撤销则忽略。"""
            if not 活跃[0]:#已撤销
                return#忽略
            活跃[0]=False#标记已撤销
            if 键 not in 自身.值表:#未命中
                return#忽略
            del 自身.值表[键]#删除
            自身.已变更()#通知投影
        return 撤销#返回撤销

    def 释放(自身):#拆卸时收集委托
        """移除每一个待处理值，并返回结算拥有方的操作。"""
        委托们=[条目.delegate for 条目 in 自身.值表.values()]#抽出委托
        自身.值表.clear()#清空域
        return 委托们#返回委托列表

Error=Exception#错误别名

内置源={#内置 Session 源
    'hooks':('session',),#会话快照钩子
    'keyedHooks':('projection',),#投影键控钩子
    'props':('sessionId',),#会话 id prop
}#内置名册

def 内置解析(绑定):#内置解析
    """按绑定解析内置源。"""
    return {#贡献
        'hooks':{'session':绑定.session},#绑定上的会话可观察源
        'keyedHooks':{'projection':lambda 键:绑定.session.projections.faceOf(键)},#按键取投影面
        'props':{'sessionId':绑定.sessionId},#稳定 id
    }#贡献结束

def 拒绝未声明(种类,名册,值表):#拒绝未在名册中的成员
    """未声明则抛。"""
    if 值表 is None:#无值
        return#跳过
    声明=list(名册 or ())#名册
    for 名称 in 值表.keys():#逐名
        if 名称 not in 声明:#未声明
            raise Error(f"uiSession.provide: undeclared {种类} '{名称}'")#抛错

def 校验贡献(描述符,贡献):#校验贡献不越界
    """钩子/键控/prop 均不得越界。"""
    拒绝未声明('hook',描述符.get('hooks') if isinstance(描述符,dict) else getattr(描述符,'hooks',None),贡献.get('hooks') if isinstance(贡献,dict) else getattr(贡献,'hooks',None))#校验钩子
    拒绝未声明('keyed hook',描述符.get('keyedHooks') if isinstance(描述符,dict) else getattr(描述符,'keyedHooks',None),贡献.get('keyedHooks') if isinstance(贡献,dict) else getattr(贡献,'keyedHooks',None))#校验键控
    拒绝未声明('prop',描述符.get('props') if isinstance(描述符,dict) else getattr(描述符,'props',None),贡献.get('props') if isinstance(贡献,dict) else getattr(贡献,'props',None))#校验 prop

def 占用标准属性(种类,名称,最终属性):#占用并查重
    """钩子映射到标准 prop 名。"""
    属性名=名称 if 种类=='prop' else 标准钩子属性名(名称)#映射
    if 属性名 in 最终属性:#重名
        raise Error(f"uiSession.provide: duplicate {种类} '{名称}' at prop '{属性名}'")#抛错
    最终属性.add(属性名)#登记

def 拷贝已声明(种类,目标,名册,值表,最终属性):#把已声明成员拷入目标
    """缺值则抛。"""
    for 名称 in (名册 or ()):#逐名
        占用标准属性(种类,名称,最终属性)#占用最终 prop 名
        值=(值表 or {}).get(名称) if isinstance(值表,dict) else None#取值
        if 值 is None and 值表 is not None and hasattr(值表,'get'):#映射取
            值=值表.get(名称)#再取
        if 值 is None:#缺值
            raise Error(f"uiSession.provide: missing {种类} '{名称}'")#缺值
        目标[名称]=值#写入

def 声明缺席(种类,目标,名册,最终属性):#缺席绑定上声明同名成员为 None
    """写缺席。"""
    for 名称 in (名册 or ()):#逐名
        占用标准属性(种类,名称,最终属性)#占用名
        目标[名称]=None#写缺席

def 描述符字段(描述符,键):#读描述符字段
    """映射或对象。"""
    if isinstance(描述符,dict):#映射
        return 描述符.get(键)#键
    return getattr(描述符,键,None)#属性

def 解析贡献(描述符,绑定):#按绑定解析贡献
    """调用 resolve。"""
    解析=描述符字段(描述符,'resolve')#解析器
    if 解析 is None and 描述符 is 内置源 or (isinstance(描述符,dict) and 描述符.get('hooks')==内置源['hooks']):#内置
        return 内置解析(绑定)#内置解析
    if callable(解析):#有解析器
        return 解析(绑定)#解析
    raise Error('uiSession.provide: descriptor missing resolve')#缺解析器

def 相同待处理交互(左,右):#按引用比较两份待处理投影
    """大小与每项引用全同。"""
    if len(左)!=len(右):#大小不同
        return False#不等
    for 会话标识,交互 in 左.items():#逐项
        if 右.get(会话标识) is not 交互:#引用不同
            return False#不等
    return True#全同

class 物化绑定:#已物化的绑定缓存
    """Controller 拥有方、物化值与释放入口。"""

    def __init__(自身,拥有方,值,释放):#构造
        """记下三件套。"""
        自身.owner=拥有方#拥有方
        自身.value=值#物化值
        自身.release=释放#释放缓存

class 会话界面:#会话作用域源名册与渲染器适配器
    """Cordis 服务：提供/待处理/作用域适配。"""

    def __init__(自身,上下文,会话们):#构造服务
        """登记服务名 uiSession。"""
        自身.ctx=上下文#Cordis 上下文
        自身.sessions=会话们#会话对象层
        自身.descriptors=[{**内置源,'resolve':内置解析}]#始终含内置源
        自身.bindings={}#按会话缓存物化绑定
        自身.absent=自身.物化缺席()#先物化缺席绑定
        自身.currentBinding=自身.解析当前()#再解析当前
        自身.currentListeners=set()#当前绑定订阅者
        自身.pendingDomains=[]#已注册待处理域
        自身.pendingSnapshot={}#待处理投影
        自身.pendingListeners=set()#待处理订阅者
        自身.pendingInteractions={#待处理可观察源
            'getSnapshot':lambda:自身.pendingSnapshot,#读当前投影
            'subscribe':自身._订待处理,#订阅
        }#待处理源结束
        自身.adapter={#作用域适配器
            'current':{#当前绑定源
                'getSnapshot':lambda:自身.currentBinding,#当前绑定快照
                'subscribe':自身._订当前,#订阅当前
            },#当前结束
            'resolve':lambda 键:自身.解析(键),#按键解析作用域
            'renderArea':渲染会话区域,#SessionProvider 渲染语义
        }#适配器结束
        def 投影寿命():#绑定投影寿命
            """列表变更刷新当前；拆卸释放全部物化。"""
            退订列表=会话们.list.subscribe(lambda:自身.发布当前())#列表变更
            def 拆卸():#拆卸
                """退订并释放。"""
                退订列表()#退订列表
                记录们=list(自身.bindings.values())#快照缓存
                自身.bindings.clear()#清空缓存
                for 记录 in 记录们:#释放全部物化
                    记录.release()#释放
            return 拆卸#返回拆卸
        上下文.effect(投影寿命,'ui-session: Session binding projection')#诊断名

    def _订当前(自身,监听):#订阅当前绑定
        """返回退订。"""
        自身.currentListeners.add(监听)#登记
        return lambda:自身.currentListeners.discard(监听)#退订

    def _订待处理(自身,监听):#订阅待处理
        """返回退订。"""
        自身.pendingListeners.add(监听)#登记
        return lambda:自身.pendingListeners.discard(监听)#退订

    def provide(自身,描述符):#登记一次会话作用域标准源贡献
        """由调用方 Cordis fiber 拥有 disposer。"""
        def 描述符寿命():#描述符寿命
            """挂上后重建；失败回滚。"""
            自身.descriptors.append(描述符)#挂上描述符
            try:#尝试重建
                自身.重建绑定()#重建全部绑定
            except Exception:#失败回滚
                自身.descriptors.pop()#失败则回滚
                raise#上抛
            def 拆卸():#拆卸
                """卸下再重建。"""
                try:#定位
                    索引=自身.descriptors.index(描述符)#定位
                except ValueError:#已不在
                    return#忽略
                自身.descriptors.pop(索引)#卸下描述符
                自身.重建绑定()#再重建
            return 拆卸#返回拆卸
        拆除=自身.ctx.effect(描述符寿命,'uiSession.provide()')#诊断名
        return lambda:拆除()#对外 disposer

    def registerPendingInteraction(自身,优先级):#登记待处理交互域
        """返回发布单个交互及其拆卸委托的函数。"""
        域=待处理交互域(优先级,lambda:自身.发布待处理交互())#构造域
        def 域寿命():#域寿命
            """挂上域并立即投影；异步拆卸先清可见值。"""
            自身.pendingDomains.append(域)#挂上域
            自身.发布待处理交互()#立即投影
            def 拆卸():#拆卸
                """先清可见值，再结算拥有方。"""
                委托们=域.释放()#先清可见值
                try:#定位
                    索引=自身.pendingDomains.index(域)#定位
                    自身.pendingDomains.pop(索引)#卸下域
                except ValueError:#已不在
                    pass#忽略
                自身.发布待处理交互()#再投影
                for 委托 in 委托们:#结算拥有方
                    委托()#执行
            return 拆卸#返回拆卸
        自身.ctx.effect(域寿命,'uiSession.registerPendingInteraction()')#诊断名
        return lambda 交互,委托:域.发布(交互,委托)#返回发布器

    def 重建绑定(自身):#描述符变更后重建全部缓存
        """失败释放半成品。"""
        缺席=自身.物化缺席()#新缺席绑定
        绑定表={}#新缓存
        try:#尝试重物化
            for 会话标识,缓存 in 自身.bindings.items():#遍历旧缓存
                绑定表[会话标识]=自身.创建物化绑定(缓存.owner)#按旧拥有方重物化
        except Exception:#失败
            for 记录 in 绑定表.values():#失败释放半成品
                记录.release()#释放
            raise#上抛
        旧=自身.bindings#旧缓存
        自身.absent=缺席#换缺席
        自身.bindings=绑定表#换缓存
        for 记录 in 旧.values():#释放旧缓存
            记录.release()#释放
        自身.发布当前()#刷新当前

    def 解析(自身,键):#按会话解析
        """无绑定则缺席。"""
        拥有方=自身.sessions.binding(键)#取 Controller 绑定
        if 拥有方 is None:#无绑定
            return None#缺席
        缓存=自身.bindings.get(键)#读缓存
        if 缓存 is not None and 缓存.owner is 拥有方:#拥有方未变
            return 缓存.value#复用
        记录=自身.创建物化绑定(拥有方)#重物化
        自身.bindings[键]=记录#写入缓存
        if 缓存 is not None:#有旧
            缓存.release()#释放旧记录
        return 记录.value#返回新值

    def 解析当前(自身):#解析当前选中
        """无选中或解析失败走缺席。"""
        当前=自身.sessions.list.getSnapshot().current#列表当前 id
        if 当前 is None:#无选中
            return 自身.absent#缺席
        return 自身.解析(当前) or 自身.absent#解析或缺席

    def 发布当前(自身):#推送当前绑定变更
        """引用未变则跳过。"""
        下一=自身.解析当前()#解析下一当前
        if 下一 is 自身.currentBinding:#引用未变
            return#跳过
        自身.currentBinding=下一#更新当前
        通知订阅者们(自身.currentListeners,'[ui-session] current binding')#通知订阅者

    def 发布待处理交互(自身):#跨域合成待处理投影
        """更大或相等优先级胜出。"""
        胜出表={}#胜出表
        for 域 in 自身.pendingDomains:#逐域
            for 交互 in 域.值快照():#逐交互
                优先级=域.优先级(交互)#算优先级
                会话标识=交互.sessionId if hasattr(交互,'sessionId') else 交互['sessionId']#所属会话
                先前=胜出表.get(会话标识)#已有胜出
                if 先前 is None or 优先级>=先前['precedence']:#更大或相等胜出
                    胜出表[会话标识]={'interaction':交互,'precedence':优先级}#写入胜出
        投影={会话标识:值['interaction'] for 会话标识,值 in 胜出表.items()}#剥掉优先级
        if 相同待处理交互(自身.pendingSnapshot,投影):#同内容
            return#跳过
        自身.pendingSnapshot=投影#更新投影
        通知订阅者们(自身.pendingListeners,'[ui-session] pending interactions')#通知

    def 创建物化绑定(自身,拥有方):#物化并挂生命周期
        """作用域死亡时清缓存。"""
        值=自身.物化(拥有方)#合并描述符
        记录箱=[None]#前向引用

        def 作用域寿命():#作用域死亡清理
            """已被替换则忽略。"""
            def 清理():#清理
                """清缓存并可能回退缺席。"""
                if 自身.bindings.get(拥有方.sessionId) is not 记录箱[0]:#已被替换
                    return#忽略
                自身.bindings.pop(拥有方.sessionId,None)#清缓存
                if 自身.currentBinding is not 值:#非当前
                    return#只清缓存
                自身.currentBinding=自身.absent#回退缺席
                通知订阅者们(自身.currentListeners,'[ui-session] current binding')#通知
            return 清理#返回清理
        释放效果=拥有方.ctx.effect(作用域寿命,f'ui-session: binding {拥有方.sessionId}')#诊断名
        记录=物化绑定(拥有方,值,lambda:释放效果())#缓存记录
        记录箱[0]=记录#前向写入
        return 记录#返回记录

    def 物化(自身,绑定):#合并全部描述符
        """拒绝未声明成员；绑 store 作用域。"""
        钩子={}#钩子表
        键控={}#键控表
        属性={}#prop 表
        最终属性=set()#最终 prop 名去重
        for 描述符 in 自身.descriptors:#逐描述符
            贡献=解析贡献(描述符,绑定)#解析贡献
            if not isinstance(贡献,dict):#对象贡献
                贡献={#归一
                    'hooks':getattr(贡献,'hooks',None),#钩子
                    'keyedHooks':getattr(贡献,'keyedHooks',None),#键控
                    'props':getattr(贡献,'props',None),#prop
                }#归一结束
            校验贡献(描述符 if isinstance(描述符,dict) else {#校验
                'hooks':描述符字段(描述符,'hooks'),#钩子名册
                'keyedHooks':描述符字段(描述符,'keyedHooks'),#键控名册
                'props':描述符字段(描述符,'props'),#prop 名册
            },贡献)#校验结束
            拷贝已声明('hook',钩子,描述符字段(描述符,'hooks'),贡献.get('hooks'),最终属性)#拷钩子
            拷贝已声明('keyed hook',键控,描述符字段(描述符,'keyedHooks'),贡献.get('keyedHooks'),最终属性)#拷键控
            拷贝已声明('prop',属性,描述符字段(描述符,'props'),贡献.get('props'),最终属性)#拷 prop
        值={#作用域绑定
            'key':绑定.sessionId,#会话键
            'ctx':绑定.ctx,#拥有 Context
            'hooks':钩子,#钩子
            'keyedHooks':键控,#键控
            'props':属性,#prop
        }#绑定结束
        自身.ctx.slots.bindStoreScope(值)#把 store 作用域绑到该绑定
        return 值#返回

    def 物化缺席(自身):#无 Session 时的缺席形状
        """声明同名成员为 None。"""
        钩子={}#缺席钩子
        键控={}#缺席键控
        属性={}#缺席 prop
        最终属性=set()#去重集
        for 描述符 in 自身.descriptors:#逐描述符
            声明缺席('hook',钩子,描述符字段(描述符,'hooks'),最终属性)#声明缺席钩子
            声明缺席('keyed hook',键控,描述符字段(描述符,'keyedHooks'),最终属性)#声明缺席键控
            声明缺席('prop',属性,描述符字段(描述符,'props'),最终属性)#声明缺席 prop
        return {'key':None,'hooks':钩子,'keyedHooks':键控,'props':属性}#键缺席

UiSession=会话界面#上游名

def 应用(上下文):#浏览器侧安装入口
    """安装会话根源与作用域适配器。"""
    服务=会话界面(上下文,上下文.sessions)#构造服务
    上下文.slots.provideRoot({#贡献根源
        'hooks':{#根钩子
            'sessions':上下文.sessions.list,#根列表源
            'sessionPendingInteraction':服务.pendingInteractions,#根待处理源
        },#钩子结束
    })#根贡献结束
    上下文.slots.installScope('session',服务.adapter)#安装 session 作用域
