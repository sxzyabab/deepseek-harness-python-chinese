from .计划 import 已提交计划

__all__=['计划定义']


def 匹配(事件):
    '命中 exit_plan_mode。PTC 结算是更新，其余是起始'
    计划=已提交计划(事件)
    if 计划 is None:
        return None
    角色='update' if 事件['type']=='tool/ptc-dispatch' else 'start'
    return {'id':计划['callId'],'role':角色}


def 起始(上下文,匹配项,读者=None):
    '起始态就是这条匹配里的已提交计划。组装器会多传读者，这份定义不读历史'
    return 已提交计划(匹配项['event'])


def 更新(上下文,匹配项=None):
    '后来的结算留在原来的卡片上，不改内容'
    return 上下文['state']


def 构建视图节点(上下文):
    '建成隐藏的聊天节点，卡片改由回合尾去读'
    起始项=上下文['start']
    if 起始项 is None and len(上下文['matches'])>0:
        起始项=上下文['matches'][0]
    数据=上下文['state']
    if 数据 is None and 起始项 is not None:
        数据=已提交计划(起始项['event'])
    if 数据 is None or 起始项 is None:
        return None
    return {
        'key':上下文['key'],
        'kind':'submitted-plan',
        'id':上下文['id'],
        'target':'chat',
        'anchorSeq':起始项['event']['seq'],
        'location':起始项['location'],
        'visibility':'hidden',
        'data':数据,
    }


计划定义={
    'kind':'submitted-plan',
    'target':'chat',
    'match':匹配,
    'start':起始,
    'update':更新,
    'buildViewNode':构建视图节点,
}
