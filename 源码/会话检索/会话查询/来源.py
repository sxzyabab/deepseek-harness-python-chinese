"""逻辑会话源观察者共用的不可变头检查。"""
from .配置 import 会话查询错误#检索错误

def 校验会话头兼容(甲,乙):
    """拒绝同一逻辑会话源上互不兼容的观察。"""
    甲深度=甲['delegationDepth'] if 'delegationDepth' in 甲 and 甲['delegationDepth'] is not None else 0#甲深度
    乙深度=乙['delegationDepth'] if 'delegationDepth' in 乙 and 乙['delegationDepth'] is not None else 0#乙深度
    if (
        甲['version']!=乙['version']
        or 甲['id']!=乙['id']
        or 甲['createdAt']!=乙['createdAt']
        or (甲['cwd'] if 'cwd' in 甲 else None)!=(乙['cwd'] if 'cwd' in 乙 else None)
        or (甲['parentSession'] if 'parentSession' in 甲 else None)!=(乙['parentSession'] if 'parentSession' in 乙 else None)
        or (甲.get('isSeeded') is True)!=(乙.get('isSeeded') is True)
        or 甲深度!=乙深度
    ):#冲突判定
        raise 会话查询错误(
            'session source headers conflict for session "'+str(甲['id'])+'"',
            'SESSION_QUERY_SOURCE_CONFLICT',
        )#抛出源冲突
