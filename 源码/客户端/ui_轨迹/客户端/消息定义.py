from .轨迹节点 import 轨迹节点#目标信封
from .轨迹表投影 import 上下文出处,上下文表单#来源投影

__all__=['登记轨迹消息定义']

空待处理={'kind':'snapshot','ids':[]}#还没有拼接
空已认领=set()#当前认领

def 登记轨迹消息定义(上下文):
    '登记轨迹收件箱分类和消息记录'
    def 收件箱匹配(事件):
        '下一步收件箱拼接才开一条'
        if 事件.get('type')=='agent/inbox/spliced' and isinstance(事件.get('data'),dict) and 事件['data'].get('target')=='next-step':
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 收件箱开始(_上下文,匹配,读取器):
        '按耐久顺序叠一条下一步拼接'
        事件=匹配['event']
        if 事件.get('type')!='agent/inbox/spliced':
            raise Exception('trajectory-inbox-next-step start requires agent/inbox/spliced')
        上一=读取器['previous']('trajectory-inbox-next-step')
        先前待处理=空待处理 if 上一 is None else (上一.get('state') or {}).get('pending') or 空待处理
        拼接=事件.get('data') or {}
        插入=[身份.get('id') for 身份 in 拼接.get('inserted') or [] if isinstance(身份,dict)]
        删除数=拼接.get('removedCount') or 0
        if 删除数>0 and 拼接.get('outcome')!='canceled':
            拼接链=[]
            当前=先前待处理
            while isinstance(当前,dict) and 当前.get('kind')=='splice':
                拼接链.append(当前)
                当前=当前.get('previous')
            待处理=list(当前.get('ids') or []) if isinstance(当前,dict) else []
            for 片 in reversed(拼接链):
                起=片.get('start') or 0
                删=片.get('removedCount') or 0
                待处理[起:起+删]=list(片.get('inserted') or [])
            被删=待处理[拼接.get('start') or 0:(拼接.get('start') or 0)+删除数]
            待处理[拼接.get('start') or 0:(拼接.get('start') or 0)+删除数]=插入
            return {'pending':{'kind':'snapshot','ids':待处理},'currentClaimed':set(被删)}
        已认领=set(() if 上一 is None else (上一.get('state') or {}).get('currentClaimed') or ())
        for 标识 in 插入:
            已认领.discard(标识)
        return {
            'pending':{
                'kind':'splice',
                'previous':先前待处理,
                'start':拼接.get('start') or 0,
                'removedCount':删除数,
                'inserted':插入,
            },
            'currentClaimed':已认领,
        }

    def 原样(上下文,_匹配=None):
        '更新不改状态'
        return 上下文.get('state')

    def 不发布(_匹配=None):
        '收件箱不进入视图'
        return 'none'

    def 消息匹配(事件):
        '用户或开发者消息各开一条'
        if 事件.get('type') in ('user/message','developer/message'):
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 消息开始(_上下文,匹配,读取器):
        '开发者消息和注入来源记成上下文；被认领的用户消息记成转向'
        事件=匹配['event']
        if 事件.get('type')=='developer/message':
            消息=(事件.get('data') or {}).get('message') or {}
            return {
                'kind':'context',
                'seq':事件.get('seq'),
                'time':事件.get('time'),
                'content':消息.get('content'),
                'source':消息.get('source'),
                'producer':上下文出处(消息.get('source')),
                'form':上下文表单(消息.get('source')),
            }
        if 事件.get('type')!='user/message':
            raise Exception('trajectory-input-message start requires user/message')
        数据=事件.get('data') or {}
        来源=数据.get('source') or {}
        if 来源.get('kind')!='user':
            return {
                'kind':'context',
                'seq':事件.get('seq'),
                'time':事件.get('time'),
                'content':数据.get('content'),
                'source':数据.get('source'),
                'producer':上下文出处(数据.get('source')),
                'form':上下文表单(数据.get('source')),
            }
        上一=读取器['previous']('trajectory-inbox-next-step')
        已认领=set() if 上一 is None else (上一.get('state') or {}).get('currentClaimed') or set()
        认领=str(数据.get('id')) in 已认领
        if 认领:
            return {
                'kind':'steering',
                'messageId':数据.get('id'),
                'seq':事件.get('seq'),
                'time':事件.get('time'),
                'content':数据.get('content'),
                'source':数据.get('source'),
            }
        return {
            'kind':'user',
            'seq':事件.get('seq'),
            'time':事件.get('time'),
            'content':数据.get('content'),
            'source':数据.get('source'),
        }

    def 消息视图(上下文):
        '有状态才贡献节点'
        if 上下文.get('state') is None:
            return None
        return 轨迹节点(上下文,上下文['state'].get('seq'),{'kind':'node','node':上下文['state']})

    上下文.uiConversation.events.register({
        'kind':'trajectory-inbox-next-step',
        'match':收件箱匹配,
        'start':收件箱开始,
        'update':原样,
        'publication':不发布,
    })
    上下文.uiConversation.events.register({
        'kind':'trajectory-input-message',
        'target':'trajectory',
        'match':消息匹配,
        'start':消息开始,
        'update':原样,
        'buildViewNode':消息视图,
    })
