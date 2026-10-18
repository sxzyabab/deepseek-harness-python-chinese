from ...异常 import 聊天错误

__all__=['下一步收件箱定义','下一回合收件箱定义']

空待定={'kind':'snapshot','ids':[]}
空已认领=set()


def 物化待定(状态):
    '把拼接链展开成当前待认领名单'
    拼接表=[]
    当前=状态
    while isinstance(当前,dict) and 当前.get('kind')=='splice':
        拼接表.append(当前)
        当前=当前.get('previous')
    待定=list(当前.get('ids') if isinstance(当前,dict) and isinstance(当前.get('ids'),list) else [])
    for 拼接 in reversed(拼接表):
        起=拼接.get('start') if isinstance(拼接.get('start'),int) else 0
        移除=拼接.get('removedCount') if isinstance(拼接.get('removedCount'),int) else 0
        插入=拼接.get('inserted') if isinstance(拼接.get('inserted'),list) else []
        待定[起:起+移除]=list(插入)
    return 待定


def 应用拼接(先前,拼接,序号):
    '按代理循环的持久顺序应用一次收件箱拼接'
    先前状态=先前.get('state') if isinstance(先前,dict) else None
    先前待定=先前状态.get('pending') if isinstance(先前状态,dict) and 先前状态.get('pending') is not None else 空待定
    插入=拼接.get('inserted') if isinstance(拼接.get('inserted'),list) else []
    移除数=拼接.get('removedCount') if 拼接.get('removedCount') is not None else 0
    if 移除数>0 and 拼接.get('outcome')!='canceled':
        待定=物化待定(先前待定)
        起=拼接.get('start') if isinstance(拼接.get('start'),int) else 0
        被移除=待定[起:起+移除数]
        待定[起:起+移除数]=list(插入)
        已认领=set()
        有人=False
        for 消息 in 被移除:
            if isinstance(消息,dict):
                已认领.add(消息.get('id'))
                来源=消息.get('source') if isinstance(消息.get('source'),dict) else {}
                if 来源.get('kind')=='user':
                    有人=True
        return {
            'pending':{'kind':'snapshot','ids':待定},
            'currentClaimed':已认领,
            'claimSeq':序号,
            'claimedHuman':有人,
        }
    已认领=先前状态.get('currentClaimed') if isinstance(先前状态,dict) and isinstance(先前状态.get('currentClaimed'),set) else set(空已认领)
    下一认领=None
    for 项 in 插入:
        if isinstance(项,dict) and 项.get('id') in 已认领:
            if 下一认领 is None:
                下一认领=set(已认领)
            下一认领.discard(项.get('id'))
    if 下一认领 is not None:
        已认领=下一认领
    return {
        'pending':{
            'kind':'splice',
            'previous':先前待定,
            'start':拼接.get('start'),
            'removedCount':移除数,
            'inserted':插入,
        },
        'currentClaimed':已认领,
        'claimSeq':先前状态.get('claimSeq') if isinstance(先前状态,dict) and 先前状态.get('claimSeq') is not None else -1,
        'claimedHuman':先前状态.get('claimedHuman') if isinstance(先前状态,dict) else False,
    }


def 收件箱定义(目标):
    '下一步或下一回合的持久收件箱。只有被认领的批次才物化'
    种类='inbox-'+目标

    def 匹配(事件):
        '只认这个目标的拼接'
        if 事件.get('type')=='agent/inbox/spliced' and isinstance(事件.get('data'),dict) and 事件['data'].get('target')==目标:
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 开始(上下文,匹配项,读取器):
        '第一笔拼接建立这条链'
        事件=匹配项.get('event') if isinstance(匹配项,dict) else None
        if not isinstance(事件,dict) or 事件.get('type')!='agent/inbox/spliced':
            raise 聊天错误('inbox start requires agent/inbox/spliced')
        先前=读取器.previous(种类)
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        return 应用拼接(先前,数据,事件.get('seq'))

    def 更新(上下文,匹配项=None):
        '收件箱定义不再改已有状态'
        return 上下文.get('state')

    def 不公布(匹配项=None):
        '收件箱状态不单独成行'
        return 'none'

    return {
        'kind':种类,
        'match':匹配,
        'start':开始,
        'update':更新,
        'publication':不公布,
    }


下一步收件箱定义=收件箱定义('next-step')
下一回合收件箱定义=收件箱定义('next-turn')
