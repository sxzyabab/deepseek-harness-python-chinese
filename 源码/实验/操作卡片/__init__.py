'回答下方的可选操作卡片：propose_action、卡片状态、用户操作和状态通知'
from ...依赖.工具 import 设置内部数据
from ...依赖.cordis.服务 import 服务
from ...依赖.cordis.纤程 import 纤程状态
from ...类型化远程调用.协议 import 远程,远程服务
from ...模型后端.llm import harness错误,创建用户消息
from ...内核.工具 import 定义工具
from ...内核.会话 import 追加插件记录
from ...基础设施.js特性 import PromiseEX as 期约
from ...基础设施.通用工具 import 紧凑json编码,是否非负安全整数,是否有限json数字
from . import 类型,投影
from .投影 import 提议动作,操作卡片投影

__all__=['配置','操作卡片','操作卡片错误','插件正在停止','类型','投影']

关闭动作='dismiss'
推导阶段=('replaced',)
终态阶段=('dismissed',)+推导阶段
技能工具='skill'
状态前言=('Latest status of action cards from user actions and background work. '
    +'These are status facts, not a request to start or retry work. Use these receipts instead of the earlier proposal when describing progress.')
状态收束='Continue with the user’s current request.'

def 会话序号(值):
    '接纳已有事件位置。内核.会话 未导出 SessionSeq'
    if isinstance(值,bool) or not 是否非负安全整数(值) or not 是否有限json数字(值):
        raise TypeError('SessionSeq must be a non-negative safe integer, got '+str(值))
    return int(值)

def 插件正在停止(所有者,正在排空):
    '纤程或祖先已拆除、正在卸载，或本插件已经开始排空'
    纤程=所有者
    while True:
        if 纤程.编号 is None or 纤程.状态==纤程状态.卸载中:
            return True
        父纤程=纤程.父上下文.纤程
        if 父纤程 is 纤程:
            return 正在排空
        纤程=父纤程

class 操作卡片错误(harness错误):
    '被拒绝的 propose_action。消息告诉模型改做什么'
    def __init__(自身,消息,码):
        '记下稳定 code'
        super().__init__(消息,码)

class 配置模式:
    '出卡上限。排队消息达到该数时拒绝 propose_action'
    def 校验数据(自身,数据=None):
        '缺省配置是空对象，排队上限默认 2'
        if 数据 is None:
            数据={}
        if not isinstance(数据,dict):
            raise TypeError('action-cards config must be an object')
        上限=2 if 'queuedMessageLimit' not in 数据 or 数据['queuedMessageLimit'] is None else 数据['queuedMessageLimit']
        if isinstance(上限,bool) or not isinstance(上限,int) or 上限<1:
            raise ValueError('queuedMessageLimit must be an integer >= 1')
        return {'queuedMessageLimit':上限}

配置=配置模式()

def 自有(记录,键):
    '只读自有项。浏览器送来的 toString 一类名字碰不到继承成员'
    if not isinstance(记录,dict) or 键 not in 记录:
        return None
    return 记录[键]

def 拒绝(原因):
    '没有改任何东西'
    return {'status':'refused','reason':原因}

def 问题文本(错误):
    '把种类模式的失败说成模型能改的字段路径'
    片段=[]
    for 项 in 错误.issues:
        路径=['details']+[str(段) for 段 in 项.get('path',[])]
        片段.append('.'.join(路径)+': '+项.get('message',''))
    return 'Invalid details: '+'; '.join(片段)

def 取(对象,键):
    '工具执行和事件载荷都可能是字典'
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else None
    return getattr(对象,键,None)

def 信号已中止(信号):
    '无信号视为未中止'
    if 信号 is None:
        return False
    if hasattr(信号,'aborted'):
        return bool(信号.aborted)
    if hasattr(信号,'is_set'):
        return 信号.is_set()
    return False

def 解析技能名(值):
    'skill 工具的 name 参数'
    if isinstance(值,dict) and isinstance(值.get('name'),str):
        return 值['name']
    return None

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

class 操作卡片(远程服务):
    '卡片工具、种类注册表、会话投影、用户操作和状态通知'
    inject=['tools','agents','sessionProjections','remoteAccess']
    Config=配置

    def __init__(自身,上下文,配置值=None):
        '登记 actionCards。直接组合且没有配置时用模式默认值'
        super().__init__(上下文,'actionCards')
        if 配置值 is None or not isinstance(配置值,dict) or 'queuedMessageLimit' not in 配置值:
            配置值=配置.校验数据({} if 配置值 is None else 配置值)
        自身.配置=配置值
        自身.所有者=上下文.纤程
        自身.投影句柄=None
        自身.种类表={}
        自身.已退役=set()
        自身.已加载={}
        自身.本轮加载={}
        自身.已接受={}
        自身.动作表={}
        自身.正在关闭=False
        设置内部数据(自身,服务.初始化,自身.初始化)
        自身.__dict__[服务.初始化]=自身.初始化

    def 初始化(自身):
        '登记投影、工具和监听。投影注册表的登记是同步的'
        自身.ctx.sessionProjections.登记(操作卡片投影)
        自身.投影句柄=操作卡片投影
        工具=定义工具({
            'name':提议动作,
            'description':'Show the user one optional action card under this answer. Call only as the skill that names the action instructs.',
            'parameters':{
                'action':{'type':'string','required':True,'description':'Action name from the skill.'},
                'title':{'type':'string','required':True,'description':'Card title.'},
                'brief':{'type':'string','required':True,'description':'What the action does, in the user\'s language.'},
                'details':{'type':'object','additionalProperties':True,'required':True,'description':'Fields the skill lists for this action.'},
            },
            'output':{
                'schema':{
                    'type':'object',
                    'additionalProperties':False,
                    'properties':{
                        'action':{'type':'string','required':True},
                        'title':{'type':'string','required':True},
                        'invitation':{'type':'string','required':True},
                    },
                },
                'render':渲染卡片,
            },
            'execute':自身._执行提议,
        })
        工具['when']=自身.是否声明
        自身.ctx.tools.登记(工具)
        自身.ctx.监听('tools/result',自身._工具结果)
        自身.ctx.监听('agent/disposed',自身._智能体已拆除)
        自身.ctx.监听('agent/pre-step',自身._步前,{'前置':True})
        def 排空():
            '卸载时不再接受新操作，并等到已开始的操作结算'
            def 拆除():
                '排空进行中的操作'
                自身.正在关闭=True
                return 期约.全部已结算(list(自身.动作表.values()))
            return 拆除
        自身.ctx.副作用(排空,'action-cards: drain user actions')

    def 登记(自身,种类):
        '为调用方的生存期登记一种操作。重复的动作名抛错'
        def 按类型(提案):
            '细节能通过种类模式才把卡片交给种类'
            细节=种类['details'].safeParse(提案['details'])
            if not 细节.success:
                return None
            卡片=dict(提案)
            卡片['details']=细节.data
            return 卡片
        对齐=种类.get('reconcile')
        def 细节问题(细节):
            '通过则没有说明'
            解析=种类['details'].safeParse(细节)
            if 解析.success:
                return None
            return 问题文本(解析.error)
        def 忽略数据(提案,载荷):
            '种类可以不记录忽略数据'
            卡片=按类型(提案)
            if 卡片 is None:
                return None
            忽略=种类.get('dismissal')
            if 忽略 is None:
                return None
            return 忽略(卡片,载荷)
        def 对齐卡片(智能体,提案):
            '细节不再合法的卡片没有可对齐的外部状态'
            盒=期约()
            if 对齐 is None:
                盒.解决(None)
                return 盒
            卡片=按类型(提案)
            if 卡片 is None:
                盒.解决(None)
                return 盒
            try:
                结果=对齐(智能体,卡片)
            except Exception as 错误:
                盒.拒绝(错误)
                return 盒
            if hasattr(结果,'然后') or hasattr(结果,'then'):
                然后(结果,盒.解决,盒.拒绝)
            else:
                盒.解决(结果)
            return 盒
        def 执行种类(智能体,提案,动词,载荷):
            '细节不再合法时，这次操作不可用'
            卡片=按类型(提案)
            if 卡片 is None:
                return 期约值(拒绝('unavailable'))
            return 期约值(种类['act'](智能体,卡片,动词,载荷))
        条目={
            'skill':种类['skill'],
            'invitation':种类['invitation'],
            'verbs':种类['verbs'],
            'openPhases':种类['openPhases'] if 'openPhases' in 种类 and 种类['openPhases'] is not None else [],
            'statusGuidance':种类.get('statusGuidance'),
            'statusFields':种类.get('statusFields'),
            'detailsIssues':细节问题,
            'dismissal':忽略数据,
            'reconcile':None if 对齐 is None else 对齐卡片,
            'act':执行种类,
        }
        def 效果():
            '同一动作名只能有一个种类'
            if 种类['action'] in 自身.种类表:
                raise ValueError('action-cards: action "'+种类['action']+'" is already registered')
            自身.种类表[种类['action']]=条目
            def 拆除():
                '卸下种类，但已开始的工作仍可记录'
                自身.种类表.pop(种类['action'],None)
                自身.已退役.add(种类['action'])
            return 拆除
        拆除器=自身.ctx.副作用(效果,'action-cards: kind '+种类['action'])
        def 卸下():
            '调用副作用拆除器'
            拆除器()
        return 卸下

    def 记录(自身,智能体,决定):
        '把决定写入会话日志。下一轮模型请求会报告它'
        if 决定['action'] not in 自身.种类表 and 决定['action'] not in 自身.已退役:
            raise ValueError('action-cards: cannot record a decision for unregistered action "'+决定['action']+'"')
        if 决定['phase'] in 推导阶段:
            raise ValueError('action-cards: phase "'+决定['phase']+'" is derived from the log and cannot be recorded')
        自身._追加(智能体,决定)

    def 视图(自身,会话):
        '读取一个会话的卡片'
        return 自身._状态(会话)['view']

    @远程('act')
    def 动作(自身,智能体,调用标识,动词,载荷=None):
        '对已记录的卡片执行用户操作。同一张卡片的并发操作共用一次处理'
        if 自身.正在停止():
            return 期约值(拒绝('closing'))
        if 智能体 not in 自身.ctx.agents.诸根():
            return 期约值(拒绝('not-live-root'))
        提案=自有(自身._状态(智能体.session)['view']['proposals'],调用标识)
        if 提案 is None:
            return 期约值(拒绝('unknown'))
        种类=自身.种类表.get(提案['action'])
        if 动词==关闭动作:
            def 跑忽略():
                '忽略这一张卡片'
                return 自身._忽略(智能体,种类,提案,载荷)
            return 自身._合并(智能体,调用标识,跑忽略)
        政策=None if 种类 is None else 自有(种类['verbs'],动词)
        if 种类 is None or 政策 is None:
            return 期约值(拒绝('unavailable'))
        if 政策.get('global') is True and not 自身.ctx.remoteAccess.是否允许({'kind':'global'}):
            return 期约值(拒绝('access-denied'))
        def 跑执行():
            '把这一次操作交给种类'
            return 自身._执行(智能体,种类,提案,动词,政策,载荷)
        return 自身._合并(智能体,调用标识,跑执行)

    def _状态(自身,会话):
        '读投影。句柄的 stateOf 在中文注册表上是 状态(会话, 键)'
        return 自身.ctx.sessionProjections.状态(会话,'actionCards')

    def _合并(自身,智能体,调用标识,跑):
        '一张卡片一次操作，跑在该智能体的发起方里'
        键=紧凑json编码([智能体.id,调用标识])
        已有=自身.动作表.get(键)
        if 已有 is not None:
            return 已有
        盒=期约()
        def 包():
            '发起方边界内启动操作'
            try:
                值=跑()
            except Exception as 错误:
                盒.拒绝(错误)
                return
            然后(期约值(值),盒.解决,盒.拒绝)
        try:
            自身.ctx.agents.带发起方(智能体,包)
        except Exception as 错误:
            盒.拒绝(错误)
        def 清(_值=None):
            '结算后离开进行中表'
            自身.动作表.pop(键,None)
        if hasattr(盒,'最终'):
            盒.最终(清)
        else:
            然后(盒,清,清)
        自身.动作表[键]=盒
        return 盒

    def _已对齐(自身,智能体,种类,提案,动词):
        '对齐失败或根已关闭时返回拒绝'
        盒=期约()
        if 种类.get('reconcile') is None:
            盒.解决(None)
            return 盒
        def 成功(_值=None):
            '对齐之后根必须还在'
            if 智能体 in 自身.ctx.agents.诸根():
                盒.解决(None)
            else:
                盒.解决(拒绝('not-live-root'))
        def 失败(错误):
            '读不到会话外状态时，这次操作不可用'
            自身.ctx.日志.警告('无法在 '+动词+' 之前对齐操作卡片 '+str(提案['callId'])+'：'+str(错误))
            盒.解决(拒绝('unavailable'))
        然后(种类['reconcile'](智能体,提案),成功,失败)
        return 盒

    def _忽略(自身,智能体,种类,提案,载荷):
        '暂不需要。种类已卸下时仍可忽略尚未开始的卡片'
        盒=期约()
        def 继续(拒绝结果):
            '对齐拒绝则到此为止'
            if 拒绝结果 is not None:
                盒.解决(拒绝结果)
                return
            决定=自有(自身._状态(智能体.session)['view']['decisions'],提案['callId'])
            开放=False if 种类 is None else 决定 is not None and 决定['phase'] in 种类['openPhases']
            if 决定 is not None and (决定['phase'] in 终态阶段 or not 开放):
                盒.解决({'status':'settled','decision':决定})
                return
            数据=None if 种类 is None else 种类['dismissal'](提案,载荷)
            已忽略={'callId':提案['callId'],'action':提案['action'],'phase':'dismissed'}
            if 数据 is not None:
                已忽略['data']=数据
            自身._追加(智能体,已忽略)
            盒.解决({'status':'settled','decision':已忽略})
        if 种类 is None:
            继续(None)
            return 盒
        然后(自身._已对齐(智能体,种类,提案,关闭动作),继续,盒.拒绝)
        return 盒

    def _执行(自身,智能体,种类,提案,动词,政策,载荷):
        '共享检查通过后交给种类'
        盒=期约()
        def 继续(拒绝结果):
            '对齐拒绝则到此为止'
            if 拒绝结果 is not None:
                盒.解决(拒绝结果)
                return
            决定=自有(自身._状态(智能体.session)['view']['decisions'],提案['callId'])
            if 决定 is not None and 决定['phase'] in 终态阶段:
                盒.解决({'status':'settled','decision':决定})
                return
            if 政策.get('writes') is True:
                沙盒=自身.ctx.获取服务('sandboxPolicy',False)
                if 沙盒 is not None and 沙盒.解析({'session':智能体.session})['mode']=='read-only':
                    盒.解决(拒绝('read-only'))
                    return
            然后(期约值(种类['act'](智能体,提案,动词,载荷)),盒.解决,盒.拒绝)
        然后(自身._已对齐(智能体,种类,提案,动词),继续,盒.拒绝)
        return 盒

    def _追加(自身,智能体,决定):
        '插件记录类型保持 plugin:action-cards/decision'
        追加插件记录(智能体.session,'plugin:action-cards/decision',决定)

    def 是否声明(自身,上下文或智能体):
        '下一步是否为这个智能体声明 propose_action'
        智能体=上下文或智能体['agent'] if isinstance(上下文或智能体,dict) else 上下文或智能体
        技能=自身.已加载.get(智能体)
        if 技能 is None:
            return False
        return any(种类['skill'] in 技能 for 种类 in 自身.种类表.values())

    def _执行提议(自身,参数,执行):
        '同步检查包成期约。拒绝时期约拒绝'
        盒=期约()
        try:
            盒.解决(自身._提议(参数,执行))
        except Exception as 错误:
            盒.拒绝(错误)
        return 盒

    def _提议(自身,参数,执行):
        '检查在线根、排队上限、本轮技能和每轮一张'
        智能体=取(执行,'agent')
        if 智能体 is None or 取(执行,'parent') is not None:
            raise 操作卡片错误('Call propose_action directly, not from code.','ACTION_CARD_NESTED')
        if 智能体 not in 自身.ctx.agents.诸根():
            raise 操作卡片错误('Cards are offered in the main conversation only.','ACTION_CARD_ROOT')
        if 自身._状态(智能体.session)['queued']>=自身.配置['queuedMessageLimit']:
            raise 操作卡片错误('The user has queued more messages; show no card and answer briefly.','ACTION_CARD_QUEUED')
        种类=自身.种类表.get(参数['action'])
        if 种类 is None:
            已登记=', '.join(自身.种类表.keys()) or 'none'
            raise 操作卡片错误('Unknown action "'+str(参数['action'])+'". Registered actions: '+已登记+'.','ACTION_CARD_UNKNOWN')
        轮次=自身.ctx.sessionProjections.状态(智能体.session,'turnBoundary')['lastTurn']
        加载=自身.本轮加载.get(智能体)
        if 加载 is None or 加载['turn']!=轮次 or 种类['skill'] not in 加载['skills']:
            raise 操作卡片错误('Load skill '+种类['skill']+' first, then call propose_action.','ACTION_CARD_SKILL')
        if 参数['title'].strip()=='' or 参数['brief'].strip()=='':
            raise 操作卡片错误('Write a title and a brief.','ACTION_CARD_BLANK')
        问题=种类['detailsIssues'](参数['details'])
        if 问题 is not None:
            raise 操作卡片错误(问题,'ACTION_CARD_DETAILS')
        已有本轮=自身.已接受.get(智能体)
        提案=自身.视图(智能体.session)['proposals'].values()
        if (已有本轮 is not None and 已有本轮['turn']==轮次) or any(卡片['turn']==轮次 for 卡片 in 提案):
            raise 操作卡片错误('One card per turn; the earlier card stands.','ACTION_CARD_LIMIT')
        自身.已接受[智能体]={'turn':轮次,'callId':取(执行,'callId')}
        return {'action':参数['action'],'title':参数['title'].strip(),'invitation':种类['invitation']}

    def 正在停止(自身):
        '所有者纤程正在停，或排空已经开始'
        return 插件正在停止(自身.所有者,自身.正在关闭)

    def _工具结果(自身,执行,结果):
        '本会话根直接调用 skill 才激活 propose_action'
        智能体=取(执行,'agent')
        if 智能体 is None:
            return
        if 取(执行,'name')==提议动作:
            已有=自身.已接受.get(智能体)
            if 取(结果,'isError') and 已有 is not None and 已有['callId']==取(执行,'callId'):
                自身.已接受.pop(智能体,None)
            return
        if 取(执行,'parent') is not None or 智能体 not in 自身.ctx.agents.诸根():
            return
        技能名=None
        if 取(执行,'name')==技能工具 and not 取(结果,'isError'):
            技能名=解析技能名(取(执行,'arguments'))
        if 技能名 is None or not any(种类['skill']==技能名 for 种类 in 自身.种类表.values()):
            return
        轮次=自身.ctx.sessionProjections.状态(智能体.session,'turnBoundary')['lastTurn']
        加载=自身.本轮加载.get(智能体)
        if 加载 is not None and 加载['turn']==轮次:
            加载['skills'].add(技能名)
        else:
            自身.本轮加载[智能体]={'turn':轮次,'skills':{技能名}}
        已有技能=自身.已加载.get(智能体)
        if 已有技能 is None:
            已有技能=set()
            自身.已加载[智能体]=已有技能
        已有技能.add(技能名)

    def _智能体已拆除(自身,事件):
        '丢掉这个智能体的内存激活'
        智能体=取(事件,'agent')
        自身.已加载.pop(智能体,None)
        自身.本轮加载.pop(智能体,None)
        自身.已接受.pop(智能体,None)

    def _步前(自身,载荷,下一步):
        '后续监听器准备好这一步之后，再追加尚未报告的决定'
        def 补上(决定):
            '拒绝、已取消或正在停止时不追加'
            return 自身._补通知(载荷,决定)
        决定=下一步()
        if hasattr(决定,'然后') or hasattr(决定,'then'):
            return 然后(决定,补上)
        return 补上(决定)

    def _补通知(自身,载荷,决定):
        '把尚未报告的决定收成一条 action-cards 通知'
        if 取(决定,'kind')=='reject' or 信号已中止(取(载荷,'signal')) or 自身.正在停止():
            return 决定
        智能体=取(载荷,'agent')
        状态=自身._状态(智能体.session)
        待报=list(状态['pendingStatus'].values())
        if len(待报)==0:
            return 决定
        回执=[]
        for 项 in 状态['view']['decisions'].values():
            if 项['callId'] in 状态['pendingStatus']:
                回执.append(项)
        指引=[]
        for 项 in 回执:
            种类=自身.种类表.get(项['action'])
            说明=None if 种类 is None else 种类.get('statusGuidance')
            if 说明 is not None and 说明 not in 指引:
                指引.append(说明)
        更新=[]
        for 项 in 回执:
            种类=自身.种类表.get(项['action'])
            字段=None if 种类 is None else 种类.get('statusFields')
            数据=项.get('data')
            if 数据 is not None and 字段 is not None:
                数据={键:值 for 键,值 in 数据.items() if 键 in 字段}
            提案=自有(状态['view']['proposals'],项['callId'])
            一行={'action':项['action'],'callId':项['callId']}
            if isinstance(提案,dict) and 'title' in 提案:
                一行['title']=提案['title']
            一行['phase']=项['phase']
            if 数据 is not None:
                一行['data']=数据
            更新.append(一行)
        文本=' '.join([状态前言]+指引+[状态收束])+'\n'+紧凑json编码(更新)
        消息=list(决定['messages'])
        消息.append(创建用户消息({
            'source':{
                'kind':'action-cards',
                'through':会话序号(max(待报)),
                'form':'notice',
                'summary':'Action card status updated',
            },
            'content':[{'type':'text','text':文本}],
        }))
        下一=dict(决定)
        下一['messages']=消息
        return 下一

def 渲染卡片(_参数,值):
    '被接受的调用告诉模型不要复述卡片，并带上种类的邀请'
    return [{'type':'text','text':'Card shown below your answer. Do not restate it. '+值['invitation']}]

inject=操作卡片.inject
Config=配置
default=操作卡片
