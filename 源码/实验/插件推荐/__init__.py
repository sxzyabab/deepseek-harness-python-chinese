'明确需求下的官方插件推荐：enable_official_plugin 卡片只提议，只有人点击才启用'
from ...依赖.工具 import 设置内部数据
from ...依赖.cordis.服务 import 服务
from ...类型化远程调用.协议 import 远程,远程服务
from ...基础设施.js特性 import PromiseEX as 期约
from ..操作卡片 import 插件正在停止
from . import 类型,技能
from .技能 import 可推荐,登记官方插件技能

__all__=['名称','依赖','插件推荐','应用','类型','技能']

名称='plugin-recommendations'
依赖=['pluginManager','agents','skills','actionCards']
动作名='enable_official_plugin'

def 自有(记录,键):
    '只读自有项'
    if not isinstance(记录,dict) or 键 not in 记录:
        return None
    return 记录[键]

def 已落定(决定):
    '决定已经生效'
    return {'status':'settled','decision':决定}

def 拒绝(原因):
    '没有改配置档'
    return {'status':'refused','reason':原因}

def 期约值(值):
    '同步值包成已解决的期约'
    if hasattr(值,'然后') or hasattr(值,'then'):
        return 值
    盒=期约()
    盒.解决(值)
    return 盒

def 然后(期,成功,失败=None):
    '期约扩展用中文方法'
    if hasattr(期,'然后'):
        return 期.然后(成功,失败)
    return 期.then(成功,失败)

class 细节模式:
    'details 只有去掉空白后的非空 name'
    def safeParse(自身,值):
        '通过则 data.name 已去掉空白'
        if not isinstance(值,dict) or not isinstance(值.get('name'),str) or len(值['name'].strip())==0:
            return type('结果',(),{'success':False,'data':None,'error':None})()
        return type('结果',(),{'success':True,'data':{'name':值['name'].strip()},'error':None})()

细节模式实例=细节模式()

class 插件推荐(远程服务):
    '卡片文本的目录查询，以及 enable_official_plugin 背后的启用'
    inject=依赖

    def __init__(自身,上下文,配置值=None):
        '登记 pluginRecommendations。这个服务没有自己的配置'
        super().__init__(上下文,'pluginRecommendations')
        自身.所有者=上下文.纤程
        自身.操作表=set()
        自身.已停止=期约()
        自身.正在关闭=False
        设置内部数据(自身,服务.初始化,自身.初始化)
        自身.__dict__[服务.初始化]=自身.初始化

    def 初始化(自身):
        '登记技能和卡片种类，卸载时排空启用'
        登记官方插件技能(自身.ctx)
        def 对齐(智能体,提案):
            '每次操作前确认被打断的启用是否已经落地'
            return 自身.跟踪(自身.确认(智能体,提案))
        def 执行(智能体,提案,_动词=None,_载荷=None):
            '点击启用'
            return 自身.跟踪(自身.启用(智能体,提案))
        自身.ctx.actionCards.登记({
            'action':动作名,
            'skill':'official-plugins',
            'details':细节模式实例,
            'invitation':'End with at most one short invitation in the user’s language to click Enable below; '
                +'do not say the plugin is already on.',
            'verbs':{'enable':{'global':True}},
            'openPhases':['failed','unconfirmed'],
            'statusGuidance':'Plugin cards: enabled means the plugin is on now, or after a DSH restart when application is restart-required; '
                +'already-enabled means it was on before; failed, or unconfirmed when a reload cut enabling off, can be retried from the card; '
                +'dismissed means the user declined it, so do not offer it again in this conversation; enabling authorizes nothing beyond that plugin.',
            'reconcile':对齐,
            'act':执行,
        })
        def 排空():
            '不再等待后续，并等到已开始的启用'
            def 拆除():
                '排空'
                自身.正在关闭=True
                自身.已停止.解决(None)
                return 期约.全部已结算(list(自身.操作表))
            return 拆除
        自身.ctx.副作用(排空,'plugin-recommendations: drain enabling')

    @远程('describe')
    def 描述(自身,智能体,调用标识):
        '读取已记录卡片当前的目录文本'
        盒=期约()
        if 自身.正在停止():
            盒.解决({'status':'refused','reason':'closing'})
            return 盒
        if 智能体 not in 自身.ctx.agents.诸根():
            盒.解决({'status':'refused','reason':'not-live-root'})
            return 盒
        提案=自有(自身.ctx.actionCards.视图(智能体.session)['proposals'],调用标识)
        细节=细节模式实例.safeParse(提案['details']) if 提案 is not None and 提案.get('action')==动作名 else None
        if 细节 is None or not 细节.success:
            盒.解决({'status':'refused','reason':'unknown'})
            return 盒
        组合包=None
        for 项 in 自身.ctx.pluginManager.列出组合包():
            if 项.get('name')==细节.data['name']:
                组合包=项
                break
        if 组合包 is None or not 可推荐(组合包):
            盒.解决({'status':'refused','reason':'unavailable'})
            return 盒
        元=组合包.get('meta') if isinstance(组合包.get('meta'),dict) else {}
        标题=元.get('title') if 元.get('title') is not None else 组合包['name']
        说明=元.get('description')
        if 说明 is None:
            说明=组合包.get('description') if 组合包.get('description') is not None else ''
        盒.解决({'status':'available','title':标题,'description':说明,'enabled':组合包.get('enabled')})
        return 盒

    def 正在停止(自身):
        '所有者正在停，或排空已经开始'
        return 插件正在停止(自身.所有者,自身.正在关闭)

    def 跟踪(自身,操作):
        '记到结算，卸载会等它'
        期=期约值(操作)
        自身.操作表.add(期)
        def 去掉(_值=None):
            '离开进行中表'
            自身.操作表.discard(期)
        if hasattr(期,'最终'):
            期.最终(去掉)
        else:
            然后(期,去掉,去掉)
        return 期

    def 确认(自身,智能体,提案):
        '未确认的卡片如果插件后来开了，就记成 enabled'
        盒=期约()
        卡片=自身.ctx.actionCards
        决定=自有(卡片.视图(智能体.session)['decisions'],提案['callId'])
        if 决定 is None or 决定.get('phase')!='unconfirmed':
            盒.解决(None)
            return 盒
        组合包=None
        for 项 in 自身.ctx.pluginManager.列出组合包():
            if 项.get('name')==提案['details']['name']:
                组合包=项
                break
        if 组合包 is not None and 组合包.get('enabled') is True:
            卡片.记录(智能体,{'callId':提案['callId'],'action':动作名,'phase':'enabled'})
        盒.解决(None)
        return 盒

    def 启用(自身,智能体,提案):
        '启用卡片上的插件一次。已启用的卡片原样落定，失败或未确认可以重试'
        盒=期约()
        卡片=自身.ctx.actionCards
        def 记下(阶段,数据=None):
            '去掉空字段后写入决定'
            if 数据 is None:
                数据={}
            字段={键:值 for 键,值 in 数据.items() if 值 is not None}
            决定={'callId':提案['callId'],'action':动作名,'phase':阶段}
            if len(字段)>0:
                决定['data']=字段
            卡片.记录(智能体,决定)
            return 已落定(决定)
        先前=自有(卡片.视图(智能体.session)['decisions'],提案['callId'])
        if 先前 is not None and 先前.get('phase') not in ('failed','unconfirmed'):
            盒.解决(已落定(先前))
            return 盒
        组合包=None
        for 项 in 自身.ctx.pluginManager.列出组合包():
            if 项.get('name')==提案['details']['name']:
                组合包=项
                break
        if 组合包 is None or not 可推荐(组合包):
            盒.解决(拒绝('unavailable'))
            return 盒
        if 自身.正在停止():
            盒.解决(拒绝('closing'))
            return 盒
        if 智能体 not in 自身.ctx.agents.诸根():
            盒.解决(拒绝('not-live-root'))
            return 盒
        if 组合包.get('enabled'):
            阶段='enabled' if 先前 is not None and 先前.get('phase')=='unconfirmed' else 'already-enabled'
            盒.解决(记下(阶段))
            return 盒
        try:
            结果=自身.ctx.pluginManager.设置组合包启用(组合包['name'],True)
        except Exception as 错误:
            自身.ctx.日志.警告('启用 '+组合包['name']+' 被拒绝：'+str(错误))
            盒.解决(记下('failed',{'errorCode':'operation-error'}))
            return 盒
        if 结果 is None or 自身.正在停止():
            记下('unconfirmed')
            盒.解决({'status':'unconfirmed','reason':'closing'})
            return 盒
        应用态=结果.get('application')
        错误码=None
        if isinstance(结果.get('error'),dict):
            错误码=结果['error'].get('code')
        盒.解决(记下('failed' if 应用态=='failed' else 'enabled',{
            'application':'restart-required' if 应用态=='restart-required' else None,
            'errorCode':错误码,
        }))
        return 盒

def 应用(上下文):
    '登记官方插件技能、enable_official_plugin 卡片种类和目录文本远程方法'
    上下文.启动插件(插件推荐)

name=名称
inject=依赖
apply=应用
