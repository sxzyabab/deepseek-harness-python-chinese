__all__=['回合过程是否打开']


def 回合过程是否打开(状态,规格,默认打开):
    '读者对当前回答代的选择优先。否则最新完成回合保持打开，更早的回合收起'
    回合=规格['turn']
    已存=None
    for 条目 in 状态['turnProcesses']:
        if 条目['turn']==回合:
            已存=条目
            break
    回答步=规格['answerStep'] if 规格.get('answerStep') is not None else 0
    if 已存 is None or 已存['answerStep']!=回答步:
        return 默认打开
    return 已存.get('collapsed') is not True
