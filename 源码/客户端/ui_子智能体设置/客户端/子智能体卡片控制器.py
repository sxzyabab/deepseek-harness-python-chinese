__all__=['子智能体卡片外壳','子智能体卡片面']

def 子智能体卡片外壳(限额,模型):
    """两节可用性与结算合成一张卡的外壳。"""
    节=[项 for 项 in (限额,模型) if 项.get('available')]
    return {
        'available':len(节)>0,
        'writable':all(项.get('writable') for 项 in 节),
        'dirty':any(项.get('dirty') for 项 in 节),
        'invalid':any(项.get('invalid') for 项 in 节) or (
            模型.get('available') and 模型.get('dirty') and 模型.get('conflicted')
        ),
        'saving':any(项.get('saving') for 项 in 节),
        'failed':any(项.get('failed') for 项 in 节),
    }

def 子智能体卡片面(限额,模型):
    """两张表单合成一次保存。"""
    def 保存():
        """校验后只写脏的那一节。"""
        限额态=限额['hooks']['subagentLimitsCard'].getSnapshot()
        模型态=模型['hooks']['subagentModelSelectionCard'].getSnapshot()
        状态=子智能体卡片外壳(限额态,模型态)
        if not 状态['available'] or not 状态['writable'] or not 状态['dirty'] or 状态['invalid'] or 状态['saving']:
            return
        if 模型态.get('available') and 模型态.get('dirty'):
            模型['save']()
        if 限额态.get('available') and 限额态.get('dirty'):
            限额['save']()
    def 丢弃():
        """保存中不可丢。"""
        if 子智能体卡片外壳(
            限额['hooks']['subagentLimitsCard'].getSnapshot(),
            模型['hooks']['subagentModelSelectionCard'].getSnapshot(),
        )['saving']:
            return
        限额['discard']()
        模型['discard']()
    return {
        'hooks':{**限额['hooks'],**模型['hooks']},
        'editLimit':限额['edit'],
        'resetLimit':限额['resetField'],
        'toggleEnabled':模型['toggleEnabled'],
        'toggleModel':模型['toggleModel'],
        'retryCatalog':模型['retryCatalog'],
        'save':保存,
        'discard':丢弃,
    }
