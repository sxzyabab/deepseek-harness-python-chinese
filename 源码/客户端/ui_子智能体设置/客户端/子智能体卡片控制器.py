__all__=['子智能体卡片外壳']

def 子智能体卡片外壳(限额,模型):
    '两节里正在服务的那些，合成一张卡的可用性与结算'
    节=[项 for 项 in (限额,模型) if 项['available']]
    return {
        'available':len(节)>0,
        'writable':all(项['writable'] for 项 in 节),
        'dirty':any(项['dirty'] for 项 in 节),
        'invalid':any(项['invalid'] for 项 in 节) or (
            模型['available'] and 模型['dirty'] and 模型['conflicted']
        ),
        'saving':any(项['saving'] for 项 in 节),
        'failed':any(项['failed'] for 项 in 节),
    }
