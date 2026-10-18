from ..异常 import 会话错误,拒绝未声明#本包异常与未声明成员
from ....依赖.cordis.服务 import 服务#服务基类
from ....基础设施.通用工具 import 获取内部数据#远程事件订阅槽
from ....工具.值 import 带值弱映射#按作用域上下文缓存物化绑定
from . import 会话提供方#同目录模块
from .会话提供方 import 渲染会话区域#会话区域选择

__all__=['依赖','应用','会话界面','会话提供方','渲染会话区域']

依赖=['sessions','slots','remote','remoteAccess']#所需的会话、槽位、远程与访问服务

def 通知订阅者(监听集合,标签):
    '按快照逐个调用。一个失败不挡住其余，失败写到控制台'
    for 监听 in list(监听集合):#先复制，回调里退订不影响这一轮
        try:#一个失败不抛出
            监听()#通知
        except Exception as 错误:#记下后继续
            print(标签+' subscriber failed:',错误)#对应 console.error

def 内置解析(绑定):
    '解析内置的会话、投影与会话标识'
    def 取投影面(键):
        '按键取该会话的投影面'
        return 绑定['session'].projections.面(键)#生产会话的投影面
    return {#这一次绑定的内置贡献
        'hooks':{'session':绑定['session']},#会话可观察对象
        'keyedHooks':{'projection':取投影面},#按键取投影
        'props':{'sessionId':绑定['sessionId']},#稳定会话标识
    }

内置源={#始终在名册最前
    'hooks':('session',),#会话钩子
    'keyedHooks':('projection',),#投影键控钩子
    'props':('sessionId',),#会话标识
    'resolve':内置解析,#内置解析器
}

def 按身份卸下(表,项):
    '按对象身份卸下一项。找不到时卸下最后一项'
    索引=-1#未找到
    下标=0#当前位置
    for 当前 in 表:#逐项比身份
        if 当前 is 项:#就是这一项
            索引=下标#记下
            break#停止
        下标+=1#下一项
    if 索引<0:#未找到
        del 表[-1:]#对应 splice(-1, 1)，空表则不动
        return#卸完
    del 表[索引:索引+1]#卸下命中的那一项

def 占用标准属性(种类,名称,最终属性):
    '占用最终属性名。重名则抛'
    if 种类=='prop':#属性名原样
        属性名=名称#不加重写
    elif 名称=='':#空钩子名
        属性名='use'#只有前缀
    else:#钩子名变成 use 加首字母大写
        属性名='use'+名称[0].upper()+名称[1:]#标准钩子属性名
    if 属性名 in 最终属性:#已经占用
        raise 会话错误(f"uiSession.provide: duplicate {种类} '{名称}' at prop '{属性名}'")#重名
    最终属性.add(属性名)#登记

def 拷贝已声明(种类,目标,名册,值表,最终属性):
    '把已声明成员写入目标。缺值则抛'
    名单=名册 if 名册 is not None else ()#没有名册就空
    for 名称 in 名单:#逐个已声明名
        占用标准属性(种类,名称,最终属性)#占用最终名
        值=None#缺省当缺失
        if 值表 is not None and 名称 in 值表:#贡献里有这个名
            值=值表[名称]#取出
        if 值 is None:#没有值
            raise 会话错误(f"uiSession.provide: missing {种类} '{名称}'")#缺值
        目标[名称]=值#写入

def 声明缺席(种类,目标,名册,最终属性):
    '缺席绑定时，已声明的名字写成空'
    名单=名册 if 名册 is not None else ()#没有名册就空
    for 名称 in 名单:#逐个已声明名
        占用标准属性(种类,名称,最终属性)#占用最终名
        目标[名称]=None#写成空

def 创建绑定源(值):
    '构造带当前值、监听集合、读快照与订阅的绑定源'
    源={'value':值,'listeners':set()}#值与监听
    def 读快照():
        '当前绑定值'
        return 源['value']#当前值
    def 订阅(监听):
        '登记监听并返回退订'
        源['listeners'].add(监听)#登记
        def 退订():
            '去掉这个监听'
            源['listeners'].discard(监听)#退订
        return 退订#退订函数
    源['getSnapshot']=读快照#读口
    源['subscribe']=订阅#订口
    return 源#绑定源

class 待处理交互域:
    '按键保存待处理交互，并用优先级函数做跨域比较'
    def __init__(自身,优先级,已变更):
        '记下优先级函数与变更通知'
        自身.优先级=优先级#越大越优先，相等时后写的胜出
        自身.已变更=已变更#变更后重投影
        自身.值表={}#键到交互与委托

    def 值快照(自身):
        '当前域的交互值，不含委托'
        结果=[]#按写入顺序
        for 条目 in 自身.值表.values():#逐条
            结果.append(条目['interaction'])#只留交互
        return 结果#交互列表

    def 发布(自身,交互,委托):
        '发布一条交互。同一个键不能发第二次'
        键=交互.key#请求键
        if 键 in 自身.值表:#已经有这个键
            raise 会话错误(f"ui-session: duplicate pending interaction key '{键}'")#重复键
        自身.值表[键]={'interaction':交互,'delegate':委托}#写入
        自身.已变更()#通知投影
        活跃={'值':True}#撤销只生效一次
        def 撤销():
            '撤销这一次发布。重复调用忽略'
            if not 活跃['值']:#已经撤销
                return#忽略
            活跃['值']=False#标记已撤销
            if 键 not in 自身.值表:#已经被拆掉
                return#不再通知
            del 自身.值表[键]#删除
            自身.已变更()#通知投影
        return 撤销#撤销函数

    def 释放(自身):
        '清空可见值，并返回仍要结算的委托'
        委托列表=[]#按写入顺序
        for 条目 in 自身.值表.values():#逐条
            委托列表.append(条目['delegate'])#抽出委托
        自身.值表.clear()#清掉可见值
        return 委托列表#交给调用方结算

class 会话界面(服务):
    '会话作用域源名册、统一状态与作用域适配器'
    def __init__(自身,上下文,会话面):
        '登记 uiSession，并开始投影主视图与状态'
        super().__init__(上下文,'uiSession')#服务名
        自身.会话面=会话面#会话对象层
        自身.描述符表=[内置源]#名册，内置始终在前
        自身.绑定表=带值弱映射()#作用域上下文到物化记录
        自身.缺席=创建绑定源(自身.物化缺席())#没有会话时的源
        自身.当前=创建绑定源(自身.缺席['value'])#主视图当前源
        自身.待处理域=[]#已登记的待处理域
        自身.待处理快照={}#每个会话胜出的待处理交互
        自身.运行态={}#每个会话最近的运行态
        自身.完成未读=set()#主视图外尚未确认的停止
        自身.状态快照={}#统一状态
        自身.状态监听=set()#状态订阅者
        自身.主视图标识=None#正在监视保留计数的会话
        def 空退订():
            '还没有主视图订阅'
            return None#无事
        自身.退主视图=空退订#主视图保留退订
        自身.活跃=True#服务还在
        def 读状态快照():
            '当前统一状态'
            return 自身.状态快照#当前表
        def 订状态(监听):
            '订阅统一状态'
            自身.状态监听.add(监听)#登记
            def 退订():
                '去掉这个状态监听'
                自身.状态监听.discard(监听)#退订
            return 退订#退订函数
        自身.sessionStatus={#根状态源，钩子名仍是 sessionStatus
            'getSnapshot':读状态快照,#读口
            'subscribe':订状态,#订口
        }
        自身.adapter={#session 作用域适配器
            'current':自身.当前,#主视图当前源
            'bindingSource':自身.绑定源,#按引用取源
            'renderArea':渲染会话区域,#有键画子树，无键画空分支
        }
        def 投影寿命():
            '列表与远程运行态驱动主视图和统一状态'
            def 列表变更主视图():
                '列表变化后重选主视图'
                自身.发布主视图()#重选
            def 列表变更状态():
                '列表变化后协调状态'
                自身.协调状态()#协调
            def 远程运行态(会话标识,运行中):
                '远程 api-session/status'
                自身.观察运行态(会话标识,运行中)#观察
            退订列表=自身.会话面.list['subscribe'](列表变更主视图)#列表到主视图
            退订状态=自身.会话面.list['subscribe'](列表变更状态)#列表到状态
            退订远程=getattr(自身.ctx.remote,'$on')('api-session/status',远程运行态)#远程运行态
            自身.发布主视图()#先投影一次主视图
            自身.协调状态()#再对齐一次状态
            def 拆卸():
                '停订阅并释放全部物化绑定'
                自身.活跃=False#之后不再投影主视图
                退订列表()#退订列表
                退订状态()#退订状态
                退订远程()#退订远程
                自身.退主视图()#退订主视图保留
                记录列表=list(自身.绑定表.values)#先抄出记录
                自身.绑定表.clear()#清空缓存
                for 记录 in 记录列表:#逐条释放
                    记录['release']()#释放作用域副作用
            return 拆卸#交给纤程
        自身.ctx.副作用(投影寿命,'ui-session: Session binding projection')#绑定投影寿命

    def 绑定源(自身,引用):
        '按会话引用取稳定源。服务已停或没有引用时返回缺席源'
        if not 自身.活跃:#服务已停
            return 自身.缺席#缺席源
        if 引用 is None:#显式没有会话
            return 自身.缺席#缺席源
        拥有方=引用.binding#引用上的绑定
        if 自身.会话面.binding(引用.sessionId) is not 拥有方:#不是这一代控制器里的绑定
            raise 会话错误('ui-session: Session reference is not active in this Controller')#代际不对
        return 自身.源为(拥有方)#取或创建

    def 提供(自身,描述符):
        '登记一份会话作用域贡献。失败时名册回到登记前'
        def 描述符寿命():
            '挂上后重建。重建失败则摘掉'
            自身.描述符表.append(描述符)#先挂上
            try:#重建全部绑定
                自身.重建绑定()#重建
            except Exception:#失败回滚
                自身.描述符表.pop()#摘掉刚挂上的
                raise#原错误继续抛
            def 拆卸():
                '卸下这份贡献再重建'
                按身份卸下(自身.描述符表,描述符)#按身份卸下
                自身.重建绑定()#再重建
            return 拆卸#交给纤程
        拆除=自身.ctx.副作用(描述符寿命,'uiSession.provide()')#登记寿命
        def 对外拆除():
            '卸下这次贡献'
            拆除()#拆除副作用
        return 对外拆除#调用方持有的拆除器

    def 登记待处理交互(自身,优先级):
        '登记一个待处理域，返回该域的发布函数'
        def 域已变更():
            '域里的交互变了，重算胜出项'
            自身.发布待处理交互()#重投影
        域=待处理交互域(优先级,域已变更)#新建域
        def 域寿命():
            '挂上域。拆卸时先清可见值，再调用各委托'
            自身.待处理域.append(域)#挂上
            自身.发布待处理交互()#立刻投影
            def 拆卸():
                '先从投影里去掉，再逐个调用委托。委托失败不挡住其余'
                委托列表=域.释放()#先清可见值
                按身份卸下(自身.待处理域,域)#卸下域
                自身.发布待处理交互()#投影已经不含这个域
                for 委托 in 委托列表:#结算每个仍在的委托
                    try:#一个失败不挡住其余
                        委托()#调用
                    except Exception as 委托错误:#对应 allSettled，失败留下但不抛
                        委托错误=委托错误#不向外抛
            return 拆卸#交给纤程
        自身.ctx.副作用(域寿命,'uiSession.registerPendingInteraction()')#域寿命
        def 发布到域(交互,委托):
            '把一条交互交给这个域'
            return 域.发布(交互,委托)#发布并返回撤销
        return 发布到域#发布函数

    def 重建绑定(自身):
        '描述符变了以后重写各源的值，全部算完才替换'
        缺席=自身.物化缺席()#新的缺席绑定
        更新=[]#先收集，避免算到一半就发出去
        for 记录 in 自身.绑定表.values:#每个已物化绑定
            更新.append({'source':记录['source'],'value':自身.物化(记录['owner'])})#新值
        自身.缺席['value']=缺席#换缺席值
        for 项 in 更新:#换各源的值
            项['source']['value']=项['value']#写入
        通知订阅者(自身.缺席['listeners'],'[ui-session] absent binding')#通知缺席源
        for 项 in 更新:#通知各会话源
            通知订阅者(项['source']['listeners'],'[ui-session] Session binding')#通知
        自身.发布主视图()#主视图跟着换

    def 源为(自身,拥有方):
        '取这个绑定已有的源，没有就物化一份'
        缓存=自身.绑定表.get(拥有方['ctx'])#按作用域上下文
        if 缓存 is not None:#已经物化过
            return 缓存['source']#复用源
        记录=自身.创建物化绑定(拥有方)#新建
        自身.绑定表.set(拥有方['ctx'],记录)#记下
        return 记录['source']#返回源

    def 发布主视图(自身):
        '当前绑定仍被主视图持有就留着，否则改到第一个主视图会话'
        if not 自身.活跃:#服务已停
            return#不再改当前源
        按标识=自身.会话面.list['getSnapshot']()['byId']#列表行
        当前标识=自身.当前['value']['key']#当前键
        当前是主=False#默认不是主视图
        if 当前标识 is not None:#有当前会话
            保留=自身.会话面.retainInfo(当前标识)['getSnapshot']()#保留计数
            主=保留['retainedBy'].get('mainView')#主视图计数
            if 主 is None:#没有这个来源
                主=0#当成 0
            当前是主=主>0#仍被主视图持有
        if 当前是主:#留在当前会话
            下一标识=当前标识#不变
        else:#找第一个主视图会话
            下一标识=None#默认没有
            for 候选 in 按标识.values():#按列表顺序
                主=候选['retainedBy'].get('mainView')#主视图计数
                if 主 is None:#没有这个来源
                    主=0#当成 0
                if 主>0:#被主视图持有
                    下一标识=候选['id']#用这一行
                    break#只取第一个
        自身.监视主视图持有(下一标识)#换监视
        if 下一标识 is None:#没有主视图会话
            拥有方=None#走缺席
        else:#有主视图会话
            拥有方=自身.会话面.binding(下一标识)#取绑定
        if 拥有方 is None:#没有绑定
            值=自身.缺席['value']#缺席值
        else:#有绑定
            值=自身.源为(拥有方)['value']#该绑定的当前值
        if 自身.当前['value'] is 值:#值没换
            return#不通知
        自身.当前['value']=值#换成新值
        通知订阅者(自身.当前['listeners'],'[ui-session] main binding')#通知主视图

    def 监视主视图持有(自身,会话标识):
        '主视图会话变了才更换保留订阅'
        if 会话标识 is 自身.主视图标识:#还是同一个
            return#不换订阅
        自身.退主视图()#退掉旧订阅
        自身.主视图标识=会话标识#记下新的
        if 会话标识 is None:#没有主视图会话
            def 空退订():
                '没有订阅可退'
                return None#无事
            自身.退主视图=空退订#空退订
            return#结束
        def 持有变更():
            '保留计数变化后重选主视图'
            自身.发布主视图()#重选
        自身.退主视图=自身.会话面.retainInfo(会话标识)['subscribe'](持有变更)#订这个会话

    def 发布待处理交互(自身):
        '每个会话留优先级最高的那一条。相等时后登记的域胜出'
        胜出表={}#会话到胜出项
        for 域 in 自身.待处理域:#按登记顺序
            for 交互 in 域.值快照():#这个域的交互
                优先级=域.优先级(交互)#算优先级
                先前=胜出表[交互.sessionId] if 交互.sessionId in 胜出表 else None#已有胜出
                if 先前 is None or 优先级>=先前['precedence']:#没有或不少于已有的
                    胜出表[交互.sessionId]={'interaction':交互,'precedence':优先级}#换胜出
        投影={}#只留交互
        for 会话标识,值 in 胜出表.items():#逐个胜出
            投影[会话标识]=值['interaction']#去掉优先级
        相同=True#先当没变
        if len(自身.待处理快照)!=len(投影):#条数不同
            相同=False#变了
        else:#条数相同再比身份
            for 会话标识,交互 in 自身.待处理快照.items():#逐条旧值
                if 投影.get(会话标识) is not 交互:#不是同一个对象
                    相同=False#变了
                    break#不用再比
        if 相同:#投影没变
            return#不刷新状态
        自身.待处理快照=投影#换投影
        自身.发布状态()#刷新统一状态

    def 观察运行态(自身,会话标识,运行中):
        '记下运行态。主视图外从运行变为停止时记完成未读'
        先前=自身.运行态[会话标识] if 会话标识 in 自身.运行态 else None#之前的值
        基线前=自身.会话面.list['getSnapshot']()['phase']=='pending'#列表基线还没到
        自身.运行态[会话标识]=运行中#写入
        if 运行中:#正在运行
            自身.完成未读.discard(会话标识)#清掉未读
        elif (先前 is True or (先前 is None and 基线前)) and not 自身.是主视图(会话标识):#主视图外停止
            自身.完成未读.add(会话标识)#记未读
        自身.发布状态()#刷新统一状态

    def 协调状态(自身):
        '按列表对齐运行态。不在 ids 里的目录行不建立运行态'
        列表=自身.会话面.list['getSnapshot']()#列表快照
        在场=set(列表['byId'].keys())#列表里出现过的标识
        for 标识 in 列表['ids']:#只有 ids 建立运行态
            行=列表['byId'][标识]#这一行
            先前=自身.运行态[标识] if 标识 in 自身.运行态 else None#之前的运行态
            if 先前 is None:#还没有基线
                自身.运行态[标识]=行['running']#直接记下，不记未读
            elif 先前!=行['running']:#和列表不一致
                自身.观察运行态(标识,行['running'])#按变化观察
        for 标识 in 在场:#出现在列表里的
            if 自身.是主视图(标识):#当前是主视图
                自身.完成未读.discard(标识)#主视图确认掉未读
        if 列表['phase']=='ready':#基线已经到了
            for 标识 in list(自身.运行态.keys()):#复制后再删
                if 标识 in 在场:#还在列表里
                    continue#留下
                del 自身.运行态[标识]#去掉幽灵运行态
                自身.完成未读.discard(标识)#去掉幽灵未读
        自身.发布状态()#刷新统一状态

    def 是主视图(自身,会话标识):
        '这一行的主视图保留计数大于 0'
        按标识=自身.会话面.list['getSnapshot']()['byId']#列表行
        行=按标识[会话标识] if 会话标识 in 按标识 else None#这一行
        if 行 is None:#列表里没有
            return False#不是主视图
        主=行['retainedBy'].get('mainView')#主视图计数
        if 主 is None:#没有这个来源
            主=0#当成 0
        return 主>0#是否持有

    def 发布状态(自身):
        '把列表、运行态、待处理和未读合成一张表。内容相同则不通知'
        列表=自身.会话面.list['getSnapshot']()#列表快照
        标识序={}#按出现顺序去重
        for 标识 in 列表['byId'].keys():#列表行
            标识序[标识]=None#占位
        for 标识 in 自身.运行态.keys():#有运行态的
            标识序[标识]=None#占位
        for 标识 in 自身.待处理快照.keys():#有待处理的
            标识序[标识]=None#占位
        for 标识 in 自身.完成未读:#有未读的
            标识序[标识]=None#占位
        下一={}#新状态表
        for 标识 in 标识序:#按上面的顺序
            下一[标识]={#这一会话的状态
                'running':自身.运行态[标识] if 标识 in 自身.运行态 else None,#运行态，没有就是空
                'pendingInteraction':自身.待处理快照[标识] if 标识 in 自身.待处理快照 else None,#胜出的待处理
                'completionUnread':标识 in 自身.完成未读,#是否未读
            }
        相同=True#先当没变
        if len(自身.状态快照)!=len(下一):#条数不同
            相同=False#变了
        else:#条数相同再比字段
            for 标识,状态 in 自身.状态快照.items():#逐条旧状态
                候选=下一.get(标识)#新状态
                if (候选 is None
                    or 候选['running']!=状态['running']
                    or 候选['pendingInteraction'] is not 状态['pendingInteraction']
                    or 候选['completionUnread']!=状态['completionUnread']):#有字段不同
                    相同=False#变了
                    break#不用再比
        if 相同:#状态没变
            return#不通知
        自身.状态快照=下一#换表
        通知订阅者(自身.状态监听,'[ui-session] Session status')#通知

    def 创建物化绑定(自身,拥有方):
        '物化一份绑定，作用域结束时把源退回缺席值'
        值=自身.物化(拥有方)#合并描述符
        自身.ctx.slots.bindStoreScope(值)#把存储作用域交给槽位
        源=创建绑定源(值)#可观察源
        记录=None#清理运行时才读到下面赋的记录
        def 作用域寿命():
            '作用域结束时回退这个源'
            def 清理():
                '仍是当前记录才从缓存去掉，源一律退回缺席'
                if 自身.绑定表.get(拥有方['ctx']) is 记录:#还是这一条
                    自身.绑定表.delete(拥有方['ctx'])#去掉
                源['value']=自身.缺席['value']#退回缺席
                通知订阅者(源['listeners'],'[ui-session] Session binding')#通知
                自身.发布主视图()#主视图可能要换
            return 清理#交给作用域纤程
        释放效果=拥有方['ctx'].副作用(作用域寿命,'ui-session: binding '+str(拥有方['sessionId']))#作用域寿命
        def 释放():
            '拆除这条绑定的作用域副作用'
            释放效果()#拆除
        记录={'owner':拥有方,'source':源,'release':释放}#缓存记录
        return 记录#交给源为去登记

    def 物化(自身,绑定):
        '把全部描述符合成一份有会话键的绑定'
        钩子={}#普通钩子
        键控={}#键控钩子
        属性={}#直接属性
        最终属性=set()#最终属性名，用来查重
        for 描述符 in 自身.描述符表:#按登记顺序
            贡献=描述符['resolve'](绑定)#解析这一份
            拒绝未声明('hook',描述符.get('hooks'),贡献.get('hooks'))#钩子不得越界
            拒绝未声明('keyed hook',描述符.get('keyedHooks'),贡献.get('keyedHooks'))#键控不得越界
            拒绝未声明('prop',描述符.get('props'),贡献.get('props'))#属性不得越界
            拷贝已声明('hook',钩子,描述符.get('hooks'),贡献.get('hooks'),最终属性)#拷贝钩子
            拷贝已声明('keyed hook',键控,描述符.get('keyedHooks'),贡献.get('keyedHooks'),最终属性)#拷贝键控
            拷贝已声明('prop',属性,描述符.get('props'),贡献.get('props'),最终属性)#拷贝属性
        return {#作用域绑定
            'key':绑定['sessionId'],#会话键
            'ctx':绑定['ctx'],#作用域上下文
            'hooks':钩子,#钩子
            'keyedHooks':键控,#键控
            'props':属性,#属性
        }

    def 物化缺席(自身):
        '没有会话时，已声明的名字仍在，值是空'
        钩子={}#空钩子
        键控={}#空键控
        属性={}#空属性
        最终属性=set()#最终属性名，用来查重
        for 描述符 in 自身.描述符表:#按登记顺序
            声明缺席('hook',钩子,描述符.get('hooks'),最终属性)#声明空钩子
            声明缺席('keyed hook',键控,描述符.get('keyedHooks'),最终属性)#声明空键控
            声明缺席('prop',属性,描述符.get('props'),最终属性)#声明空属性
        return {'key':None,'hooks':钩子,'keyedHooks':键控,'props':属性}#没有会话键

    bindingSource=绑定源#跨包仍用上游方法名
    provide=提供#跨包仍用上游方法名
    registerPendingInteraction=登记待处理交互#跨包仍用上游方法名

def 应用(上下文,配置=None):
    '安装会话根源、session 作用域，以及当前会话的访问源'
    服务=会话界面(上下文,上下文.sessions)#构造并登记 uiSession
    def 持有信息(键):
        '按会话标识读保留信息源'
        return 上下文.sessions.retainInfo(键)#保留源
    def 会话访问(会话标识,动作=None):
        '没有动作就没有源'
        if 动作 is None:#调用方没给动作
            return None#没有可观察源
        return 上下文.remoteAccess.来源('session',会话标识,动作)#该会话这个动作的源
    上下文.slots.provideRoot({#根标准源
        'hooks':{#根钩子
            'sessions':上下文.sessions.list,#会话列表
            'sessionStatus':服务.sessionStatus,#统一状态
        },
        'keyedHooks':{#根键控钩子
            'sessionRetainInfo':持有信息,#保留信息
            'sessionAccess':会话访问,#会话访问
        },
    })
    上下文.slots.installScope('session',服务.adapter)#安装 session 作用域
    def 解析访问(绑定):
        '当前会话的 access 键控源'
        def 访问(动作):
            '按动作读这个会话的访问源'
            return 上下文.remoteAccess.来源('session',绑定['sessionId'],动作)#同一套访问源
        return {'keyedHooks':{'access':访问}}#只贡献 access
    服务.提供({#会话作用域访问
        'keyedHooks':['access'],#键控名
        'resolve':解析访问,#按绑定解析
    })

inject=依赖#框架槽
apply=应用#框架槽
