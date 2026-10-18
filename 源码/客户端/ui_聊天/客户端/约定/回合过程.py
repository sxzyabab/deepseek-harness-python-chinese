__all__=['回合过程规格相同','是子智能体委派工具','回合过程始终打开']


def 回合过程规格相同(左,右):
    '两份回合过程规格的公布字段都一样'
    return (
        左['turn']==右['turn']
        and 左['controlAnchorSeq']==右['controlAnchorSeq']
        and 左['processStartSeq']==右['processStartSeq']
        and 左['answerAnchorSeq']==右['answerAnchorSeq']
        and 左['answerStep']==右['answerStep']
        and 左['inlineReasoning']==右['inlineReasoning']
        and 左['messageCount']==右['messageCount']
        and 左['toolCallCount']==右['toolCallCount']
        and 左['subagentCount']==右['subagentCount']
    )


def 是子智能体委派工具(名称):
    '出厂委派名和它的配置变体。send_message、list_agents 这类控制工具不是'
    return 名称=='subagent' or (isinstance(名称,str) and 名称.startswith('subagent_'))


def 回合过程始终打开(节点):
    '进行中、已停止、失败的回合不能整段收起'
    if not isinstance(节点,dict):
        return False
    位置=节点.get('location')
    if not isinstance(位置,dict):
        return False
    if 位置.get('kind') not in ('turn','step'):
        return False
    回合=位置.get('turn')
    if not isinstance(回合,dict):
        return False
    结束=回合.get('end')
    原因=None
    if isinstance(结束,dict):
        数据=结束.get('data')
        if isinstance(数据,dict):
            原因体=数据.get('reason')
            if isinstance(原因体,dict):
                原因=原因体.get('kind')
    return 回合.get('status')=='open' or 原因 in ('aborted','interrupted','error')
