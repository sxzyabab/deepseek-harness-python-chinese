from ...存储 import 通知订阅者#订阅者通知
from .会话提供方 import 渲染会话区域#SessionProvider 渲染语义

__all__=[#仅中文公开名
    '注入','应用','会话界面','会话错误','待处理交互基座','标准钩子属性名',
    '内置源','相同待处理交互','相同会话状态',
]#公开面结束

注入=['sessions','slots','remote']#所需的 Controller、渲染器与远程服务

def 标准钩子属性名(名称):#钩子到标准 prop 名
    """`session` → `useSession`。"""
    if 名称 is None or 名称=='':#空
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
        键=交互.key#待处理交互基座
        if 键 in 自身.值表:#重复
            raise 会话错误("ui-session: duplicate pending interaction key '"+str(键)+"'")#重复键
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
        委托列表=[条目.delegate for 条目 in 自身.值表.values()]#抽出委托
        自身.值表.clear()#清空域
        return 委托列表#返回委托列表

class 会话错误(Exception):
    """本包会话适配失败。"""

内置源={#内置 Session 源
    'hooks':('session',),#会话快照钩子
    'keyedHooks':('projection',),#投影键控钩子
    'props':('sessionId',),#会话 id prop
}#内置名册

def 内置解析(绑定):#内置解析
    """按绑定解析内置源。"""
    def 取投影面(键):#按键取投影面
        """绑定会话的投影面。"""
        return 绑定.session.projections.faceOf(键)#投影
    return {#贡献
        'hooks':{'session':绑定.session},#绑定上的会话可观察源
        'keyedHooks':{'projection':取投影面},#按键取投影面
        'props':{'sessionId':绑定.sessionId},#稳定 id
    }#贡献结束

def 拒绝未声明(种类,名册,值表):#拒绝未在名册中的成员
    """未声明则抛。"""
    if 值表 is None:#无值
        return#跳过
    声明=list(名册 if 名册 is not None else ())#名册
    for 名称 in 值表.keys():#逐名
        if 名称 not in 声明:#未声明
            raise 会话错误("uiSession.provide: undeclared "+种类+" '"+str(名称)+"'")#抛错

def 校验贡献(描述符,贡献):#校验贡献不越界
    """钩子/键控/prop 均不得越界。"""
    拒绝未声明('hook',描述符['hooks'] if 'hooks' in 描述符 else None,贡献['hooks'] if 'hooks' in 贡献 else None)#校验钩子
    拒绝未声明('keyed hook',描述符['keyedHooks'] if 'keyedHooks' in 描述符 else None,贡献['keyedHooks'] if 'keyedHooks' in 贡献 else None)#校验键控
    拒绝未声明('prop',描述符['props'] if 'props' in 描述符 else None,贡献['props'] if 'props' in 贡献 else None)#校验 prop

def 占用标准属性(种类,名称,最终属性):#占用并查重
    """钩子映射到标准 prop 名。"""
    属性名=名称 if 种类=='prop' else 标准钩子属性名(名称)#映射
    if 属性名 in 最终属性:#重名
        raise 会话错误("uiSession.provide: duplicate "+种类+" '"+str(名称)+"' at prop '"+str(属性名)+"'")#抛错
    最终属性.add(属性名)#登记

def 拷贝已声明(种类,目标,名册,值表,最终属性):#把已声明成员拷入目标
    """缺值则抛。"""
    for 名称 in (名册 if 名册 is not None else ()):#逐名
        占用标准属性(种类,名称,最终属性)#占用最终 prop 名
        值=值表[名称] if 值表 is not None and 名称 in 值表 else None#取值
        if 值 is None:#缺值
            raise 会话错误("uiSession.provide: missing "+种类+" '"+str(名称)+"'")#缺值
        目标[名称]=值#写入

def 声明缺席(种类,目标,名册,最终属性):#缺席绑定上声明同名成员为 None
    """写缺席。"""
    for 名称 in (名册 if 名册 is not None else ()):#逐名
        占用标准属性(种类,名称,最终属性)#占用名
        目标[名称]=None#写缺席

def 解析贡献(描述符,绑定):#按绑定解析贡献
    """调用 resolve。描述符为 dict。"""
    解析=描述符['resolve'] if 'resolve' in 描述符 else None#解析器
    if 解析 is None and 描述符 is 内置源:#内置
        return 内置解析(绑定)#内置解析
    if 解析 is None and 'hooks' in 描述符 and 描述符['hooks']==内置源['hooks']:#内置形
        return 内置解析(绑定)#内置解析
    if 解析 is not None:#有解析器
        return 解析(绑定)#解析
    raise 会话错误('uiSession.provide: descriptor missing resolve')#缺解析器

def 相同待处理交互(左,右):#按引用比较两份待处理投影
    """大小与每项引用全同。"""
    if len(左)!=len(右):#大小不同
        return False#不等
    for 会话标识,交互 in 左.items():#逐项
        if 会话标识 not in 右 or 右[会话标识] is not 交互:#引用不同
            return False#不等
    return True#全同

def 相同会话状态(左,右):#比较统一状态投影
    """大小与 running/pending/unread 全同。"""
    if len(左)!=len(右):#大小不同
        return False#不等
    for 会话标识,状态 in 左.items():#逐项
        if 会话标识 not in 右:#缺右侧
            return False#不等
        候选=右[会话标识]#右侧行
        if 候选.get('running')!=状态.get('running'):#运行态不同
            return False#不等
        if 候选.get('pendingInteraction') is not 状态.get('pendingInteraction'):#待处理不同
            return False#不等
        if 候选.get('completionUnread')!=状态.get('completionUnread'):#未读不同
            return False#不等
    return True#全同

def 创建绑定源(值):#构造可观察绑定源
    """value/listeners/getSnapshot/subscribe。"""
    源={'value':值,'listeners':set()}#源对象
    def 读快照():#读快照
        """当前值。"""
        return 源['value']#值
    def 订阅(监听):#订阅
        """返回退订。"""
        源['listeners'].add(监听)#登记
        def 退订():#退订
            """去掉监听。"""
            源['listeners'].discard(监听)#去掉
        return 退订#退订
    源['getSnapshot']=读快照#挂读
    源['subscribe']=订阅#挂订
    return 源#返回源

class 物化绑定:#已物化的绑定缓存
    """Controller 拥有方、可观察源与释放入口。"""

    def __init__(自身,拥有方,源,释放):#构造
        """记下三件套。"""
        自身.owner=拥有方#拥有方
        自身.source=源#可观察源
        自身.release=释放#释放缓存

class 会话界面:#会话作用域源名册与渲染器适配器
    """Cordis 服务：提供/待处理/状态/作用域适配。"""

    def __init__(自身,上下文,会话面):#构造服务
        """登记服务名 uiSession。"""
        自身.ctx=上下文#Cordis 上下文
        自身.sessions=会话面#会话对象层
        自身.descriptors=[{**内置源,'resolve':内置解析}]#始终含内置源
        自身.bindings={}#按拥有方缓存物化绑定
        自身.absent=创建绑定源(自身.物化缺席())#先物化缺席源
        自身.current=创建绑定源(自身.absent['value'])#再构造当前源
        自身.pendingDomains=[]#已注册待处理域
        自身.pendingSnapshot={}#待处理投影
        自身.running={}#运行态表
        自身.completionUnread=set()#完成未读集
        自身.statusSnapshot={}#状态投影
        自身.statusListeners=set()#状态订阅者
        自身.mainRetainId=None#主视图持有会话
        自身.disposeMainRetain=lambda:None#主视图持有退订
        自身.active=True#服务是否活跃
        自身.sessionStatus={#状态可观察源
            'getSnapshot':自身.读状态快照,#读当前投影
            'subscribe':自身._订状态,#订阅
        }#状态源结束
        自身.adapter={#作用域适配器
            'current':自身.current,#当前绑定源
            'bindingSource':自身.取绑定源,#按引用取源
            'renderArea':渲染会话区域,#SessionProvider 渲染语义
        }#适配器结束
        def 投影寿命():#绑定投影寿命
            """列表变更刷新主视图与状态；远程运行态观察。"""
            def 列表变更主视图():#列表变更
                """刷新主视图绑定。"""
                自身.发布主视图()#刷新
            def 列表变更状态():#列表变更
                """协调状态。"""
                自身.协调状态()#协调
            def 远程运行态(会话标识,运行中):#远程事件
                """观察运行态。"""
                自身.观察运行态(会话标识,运行中)#观察
            退订列表=会话面.list.subscribe(列表变更主视图)#列表→主视图
            退订状态=会话面.list.subscribe(列表变更状态)#列表→状态
            退订远程=上下文.remote.$on('api-session/status',远程运行态)#远程运行态
            自身.发布主视图()#首次主视图
            自身.协调状态()#首次状态
            def 拆卸():#拆卸
                """标死并释放。"""
                自身.active=False#标死
                退订列表()#退订列表
                退订状态()#退订状态
                退订远程()#退订远程
                自身.disposeMainRetain()#退订主视图持有
                记录列表=list(自身.bindings.values())#快照缓存
                自身.bindings.clear()#清空缓存
                for 记录 in 记录列表:#释放全部物化
                    记录.release()#释放
            return 拆卸#返回拆卸
        上下文.副作用(投影寿命,'ui-session: Session binding projection')#诊断名

    def 读状态快照(自身):#状态投影
        """当前统一 Session UI 状态。"""
        return 自身.statusSnapshot#投影

    def _订状态(自身,监听):#订阅状态
        """返回退订。"""
        自身.statusListeners.add(监听)#登记
        def 退订():#退订
            """去掉监听。"""
            自身.statusListeners.discard(监听)#去掉
        return 退订#退订

    def 取绑定源(自身,引用):#按引用取稳定渲染器源
        """缺席或服务已死回退缺席源。"""
        if not 自身.active:#已死
            return 自身.absent#缺席
        if 引用 is None:#显式缺席
            return 自身.absent#缺席
        拥有方=引用.binding#拥有方
        if 自身.sessions.binding(引用.sessionId) is not 拥有方:#代际不匹配
            raise 会话错误('ui-session: Session reference is not active in this Controller')#抛错
        return 自身.源为(拥有方)#取或创建源

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
        拆除=自身.ctx.副作用(描述符寿命,'uiSession.provide()')#诊断名
        def 对外拆除():#对外 disposer
            """执行 effect 拆除。"""
            拆除()#拆除
            return None#无返回
        return 对外拆除#对外 disposer

    def registerPendingInteraction(自身,优先级):#登记待处理交互域
        """返回发布单个交互及其拆卸委托的函数。"""
        def 域已变更():#域变更
            """重投影待处理。"""
            自身.发布待处理交互()#投影
        域=待处理交互域(优先级,域已变更)#构造域
        def 域寿命():#域寿命
            """挂上域并立即投影；拆卸先清可见值。"""
            自身.pendingDomains.append(域)#挂上域
            自身.发布待处理交互()#立即投影
            def 拆卸():#拆卸
                """先清可见值，再结算拥有方。"""
                委托列表=域.释放()#先清可见值
                try:#定位
                    索引=自身.pendingDomains.index(域)#定位
                    自身.pendingDomains.pop(索引)#卸下域
                except ValueError:#已不在
                    pass#忽略
                自身.发布待处理交互()#再投影
                for 委托 in 委托列表:#结算拥有方
                    委托()#执行
            return 拆卸#返回拆卸
        自身.ctx.副作用(域寿命,'uiSession.registerPendingInteraction()')#诊断名
        def 发布到域(交互,委托):#发布单个交互
            """转调域.发布。"""
            return 域.发布(交互,委托)#发布
        return 发布到域#返回发布器

    def 重建绑定(自身):#描述符变更后重建全部缓存
        """更新各源值并通知。"""
        缺席=自身.物化缺席()#新缺席绑定
        更新表=[{'source':记录.source,'value':自身.物化(记录.owner)} for 记录 in 自身.bindings.values()]#收集更新
        自身.absent['value']=缺席#换缺席值
        for 项 in 更新表:#换各源值
            项['source']['value']=项['value']#写入
        通知订阅者(自身.absent['listeners'],'[ui-session] absent binding')#通知缺席
        for 项 in 更新表:#通知各绑定
            通知订阅者(项['source']['listeners'],'[ui-session] Session binding')#通知
        自身.发布主视图()#刷新主视图

    def 源为(自身,拥有方):#取或创建绑定源
        """命中缓存则复用。"""
        缓存=自身.bindings[拥有方] if 拥有方 in 自身.bindings else None#读缓存
        if 缓存 is not None:#命中
            return 缓存.source#复用
        记录=自身.创建物化绑定(拥有方)#创建
        自身.bindings[拥有方]=记录#写入
        return 记录.source#返回源

    def 发布主视图(自身):#推送主视图绑定
        """按 mainView 持有选择当前。"""
        if not 自身.active:#已死
            return#跳过
        按标识=自身.sessions.list.getSnapshot().byId#列表索引
        当前标识=自身.current['value'].get('key') if isinstance(自身.current['value'],dict) else getattr(自身.current['value'],'key',None)#当前键
        当前是主=当前标识 is not None and (自身.sessions.retainInfo(当前标识).getSnapshot().get('retainedBy',{}).get('mainView',0) or 0)>0#当前是否主视图
        if 当前是主:#保持当前
            下一标识=当前标识#保持
        else:#找主视图持有
            下一标识=None#默认无
            for 候选 in 按标识.values():#逐行
                持有=候选.get('retainedBy',{}) if isinstance(候选,dict) else getattr(候选,'retainedBy',{})#持有图
                if (持有.get('mainView',0) if isinstance(持有,dict) else 0)>0:#主视图持有
                    下一标识=候选.get('id') if isinstance(候选,dict) else getattr(候选,'id',None)#取 id
                    break#找到
        自身.监视主视图持有(下一标识)#监视
        拥有方=None if 下一标识 is None else 自身.sessions.binding(下一标识)#取拥有方
        值=自身.absent['value'] if 拥有方 is None else 自身.源为(拥有方)['value']#下一值
        if 自身.current['value'] is 值:#未变
            return#跳过
        自身.current['value']=值#更新当前
        通知订阅者(自身.current['listeners'],'[ui-session] main binding')#通知

    def 监视主视图持有(自身,会话标识):#监视主视图持有变更
        """id 未变则跳过。"""
        if 会话标识 is 自身.mainRetainId:#未变
            return#跳过
        自身.disposeMainRetain()#退订旧
        自身.mainRetainId=会话标识#记下新 id
        if 会话标识 is None:#无
            自身.disposeMainRetain=lambda:None#空
        else:#有
            def 持有变更():#持有变更
                """刷新主视图。"""
                自身.发布主视图()#刷新
            自身.disposeMainRetain=自身.sessions.retainInfo(会话标识).subscribe(持有变更)#订阅

    def 发布待处理交互(自身):#跨域合成待处理投影
        """更大或相等优先级胜出。"""
        胜出表={}#胜出表
        for 域 in 自身.pendingDomains:#逐域
            for 交互 in 域.值快照():#逐交互
                优先级=域.优先级(交互)#算优先级
                会话标识=交互.sessionId#所属会话
                先前=胜出表[会话标识] if 会话标识 in 胜出表 else None#已有胜出
                if 先前 is None or 优先级>=先前['precedence']:#更大或相等胜出
                    胜出表[会话标识]={'interaction':交互,'precedence':优先级}#写入胜出
        投影={会话标识:值['interaction'] for 会话标识,值 in 胜出表.items()}#剥掉优先级
        if 相同待处理交互(自身.pendingSnapshot,投影):#同内容
            return#跳过
        自身.pendingSnapshot=投影#更新投影
        自身.发布状态()#刷新统一状态

    def 观察运行态(自身,会话标识,运行中):#观察运行态变更
        """主视图外停止记完成未读。"""
        先前=自身.running[会话标识] if 会话标识 in 自身.running else None#先前值
        基线前=自身.sessions.list.getSnapshot().get('phase')=='pending'#基线前
        自身.running[会话标识]=运行中#写入
        if 运行中:#运行
            自身.completionUnread.discard(会话标识)#清未读
        elif (先前 is True or (先前 is None and 基线前)) and not 自身.是主视图(会话标识):#主视图外停止
            自身.completionUnread.add(会话标识)#记未读
        自身.发布状态()#刷新状态

    def 协调状态(自身):#按列表协调运行态与未读
        """就绪后清幽灵。"""
        列表=自身.sessions.list.getSnapshot()#列表快照
        在场=set(列表.get('byId',{}).keys())#在场 id
        for 标识 in 在场:#逐在场
            行=列表['byId'][标识]#行
            先前=自身.running[标识] if 标识 in 自身.running else None#先前运行态
            运行=行.get('running') if isinstance(行,dict) else getattr(行,'running',None)#行运行态
            if 先前 is None:#基线
                自身.running[标识]=运行#写入
            elif 先前!=运行:#差异
                自身.观察运行态(标识,运行)#观察
            持有=行.get('retainedBy',{}) if isinstance(行,dict) else getattr(行,'retainedBy',{})#持有
            if (持有.get('mainView',0) if isinstance(持有,dict) else 0)>0:#主视图
                自身.completionUnread.discard(标识)#清未读
        if 列表.get('phase')=='ready':#就绪后清幽灵
            for 标识 in list(自身.running.keys()):#逐运行态键
                if 标识 in 在场:#仍在场
                    continue#跳过
                del 自身.running[标识]#删运行态
                自身.completionUnread.discard(标识)#删未读
        自身.发布状态()#刷新状态

    def 是主视图(自身,会话标识):#是否主视图持有
        """mainView 计数大于 0。"""
        行=自身.sessions.list.getSnapshot().get('byId',{}).get(会话标识)#行
        if 行 is None:#无行
            return False#否
        持有=行.get('retainedBy',{}) if isinstance(行,dict) else getattr(行,'retainedBy',{})#持有
        return (持有.get('mainView',0) if isinstance(持有,dict) else 0)>0#主视图

    def 发布状态(自身):#合成统一 Session UI 状态
        """并集 id 后投影。"""
        列表标识=list(自身.sessions.list.getSnapshot().get('byId',{}).keys())#列表
        标识集=set(列表标识)|set(自身.running.keys())|set(自身.pendingSnapshot.keys())|set(自身.completionUnread)#并集
        下一={}#下一投影
        for 标识 in 标识集:#逐 id
            下一[标识]={#状态行
                'running':自身.running[标识] if 标识 in 自身.running else None,#运行态
                'pendingInteraction':自身.pendingSnapshot[标识] if 标识 in 自身.pendingSnapshot else None,#待处理
                'completionUnread':标识 in 自身.completionUnread,#未读
            }#行结束
        if 相同会话状态(自身.statusSnapshot,下一):#同内容
            return#跳过
        自身.statusSnapshot=下一#更新投影
        通知订阅者(自身.statusListeners,'[ui-session] Session status')#通知

    def 创建物化绑定(自身,拥有方):#物化并挂生命周期
        """作用域死亡时清缓存并回退缺席值。"""
        值=自身.物化(拥有方)#合并描述符
        自身.ctx.slots.bindStoreScope(值)#绑 store 作用域
        源=创建绑定源(值)#可观察源
        记录箱=[None]#前向引用

        def 作用域寿命():#作用域死亡清理
            """已被替换则忽略。"""
            def 清理():#清理
                """清缓存并刷新主视图。"""
                if 拥有方 not in 自身.bindings or 自身.bindings[拥有方] is not 记录箱[0]:#已被替换
                    return#忽略
                del 自身.bindings[拥有方]#清缓存
                源['value']=自身.absent['value']#回退缺席值
                通知订阅者(源['listeners'],'[ui-session] Session binding')#通知
                自身.发布主视图()#刷新主视图
            return 清理#返回清理
        释放效果=拥有方.ctx.副作用(作用域寿命,'ui-session: binding '+str(拥有方.sessionId))#诊断名
        def 释放():#释放缓存
            """执行绑定 effect 拆除。"""
            释放效果()#拆除
            return None#无返回
        记录=物化绑定(拥有方,源,释放)#缓存记录
        记录箱[0]=记录#前向写入
        return 记录#返回记录

    def 物化(自身,绑定):#合并全部描述符
        """拒绝未声明成员。"""
        钩子={}#钩子表
        键控={}#键控表
        属性={}#prop 表
        最终属性=set()#最终 prop 名去重
        for 描述符 in 自身.descriptors:#逐描述符
            贡献=解析贡献(描述符,绑定)#解析贡献
            校验贡献(描述符,贡献)#校验
            拷贝已声明('hook',钩子,描述符['hooks'] if 'hooks' in 描述符 else None,贡献['hooks'] if 'hooks' in 贡献 else None,最终属性)#拷钩子
            拷贝已声明('keyed hook',键控,描述符['keyedHooks'] if 'keyedHooks' in 描述符 else None,贡献['keyedHooks'] if 'keyedHooks' in 贡献 else None,最终属性)#拷键控
            拷贝已声明('prop',属性,描述符['props'] if 'props' in 描述符 else None,贡献['props'] if 'props' in 贡献 else None,最终属性)#拷 prop
        return {#作用域绑定
            'key':绑定.sessionId,#会话键
            'ctx':绑定.ctx,#拥有 Context
            'hooks':钩子,#钩子
            'keyedHooks':键控,#键控
            'props':属性,#prop
        }#绑定结束

    def 物化缺席(自身):#无 Session 时的缺席形状
        """声明同名成员为 None。"""
        钩子={}#缺席钩子
        键控={}#缺席键控
        属性={}#缺席 prop
        最终属性=set()#去重集
        for 描述符 in 自身.descriptors:#逐描述符
            声明缺席('hook',钩子,描述符['hooks'] if 'hooks' in 描述符 else None,最终属性)#声明缺席钩子
            声明缺席('keyed hook',键控,描述符['keyedHooks'] if 'keyedHooks' in 描述符 else None,最终属性)#声明缺席键控
            声明缺席('prop',属性,描述符['props'] if 'props' in 描述符 else None,最终属性)#声明缺席 prop
        return {'key':None,'hooks':钩子,'keyedHooks':键控,'props':属性}#键缺席

def 应用(上下文):#浏览器侧安装入口
    """安装会话根源与作用域适配器。"""
    服务=会话界面(上下文,上下文.sessions)#构造服务
    def 持有信息(键):#键控持有信息
        """转调 Controller。"""
        return 上下文.sessions.retainInfo(键)#持有
    上下文.slots.provideRoot({#贡献根源
        'hooks':{#根钩子
            'sessions':上下文.sessions.list,#根列表源
            'sessionStatus':服务.sessionStatus,#根状态源
        },#钩子结束
        'keyedHooks':{#键控根钩子
            'sessionRetainInfo':持有信息,#持有信息
        },#键控结束
    })#根贡献结束
    上下文.slots.installScope('session',服务.adapter)#安装 session 作用域

inject=注入#框架槽
apply=应用#框架槽
