__all__=['插话历史']


class 插话历史:
    '从持久收件箱拼接里认出下一步认领过的用户插话'
    def __init__(自身):
        '两份收件箱和已认领的下一步标识'
        自身.收件箱={'next-turn':[],'next-step':[]}
        自身.已认领下一步=set()

    def reset(自身):
        '重放窗口前清掉'
        自身.收件箱['next-turn']=[]
        自身.收件箱['next-step']=[]
        自身.已认领下一步.clear()

    def apply(自身,事件):
        '返回真只表示这条 user/message 先前从 next-step 认领，且来源是用户'
        if not isinstance(事件,dict):
            return False
        if 事件.get('type')=='agent/inbox/spliced':
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
            自身.应用拼接(数据)
            return False
        if 事件.get('type')!='user/message':
            return False
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        标识=数据.get('id')
        if 标识 not in 自身.已认领下一步:
            return False
        自身.已认领下一步.discard(标识)
        来源=数据.get('source') if isinstance(数据.get('source'),dict) else {}
        return 来源.get('kind')=='user'

    def 应用拼接(自身,拼接):
        '重放宿主已经校验过的一次拼接'
        目标=拼接.get('target')
        列=自身.收件箱.get(目标)
        if 列 is None:
            return
        起=拼接.get('start') if isinstance(拼接.get('start'),int) else 0
        移除=拼接.get('removedCount') if 拼接.get('removedCount') is not None else 0
        插入=拼接.get('inserted') if isinstance(拼接.get('inserted'),list) else []
        被移除=列[起:起+移除]
        列[起:起+移除]=list(插入)
        for 身份 in 插入:
            if isinstance(身份,dict):
                自身.已认领下一步.discard(身份.get('id'))
        if 目标!='next-step' or 拼接.get('outcome')=='canceled':
            return
        for 身份 in 被移除:
            if isinstance(身份,dict):
                自身.已认领下一步.add(身份.get('id'))
