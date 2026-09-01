"""逻辑会话源观察者共用的不可变头检查。对齐上游 `session-query/src/sources.ts`。"""
from .配置 import 会话查询错误#检索错误

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 断言会话头兼容(甲,乙):#断言两份头同属一源
    """拒绝同一逻辑会话源上互不兼容的观察。"""
    if (#任一身份字段不一致
        取字段(甲,'version')!=取字段(乙,'version')
        or 取字段(甲,'id')!=取字段(乙,'id')
        or 取字段(甲,'createdAt')!=取字段(乙,'createdAt')
        or 取字段(甲,'cwd')!=取字段(乙,'cwd')
        or 取字段(甲,'parentSession')!=取字段(乙,'parentSession')
        or 取字段(甲,'seedLength')!=取字段(乙,'seedLength')
        or (取字段(甲,'delegationDepth') or 0)!=(取字段(乙,'delegationDepth') or 0)
    ):#冲突判定
        raise 会话查询错误(#源观察打架
            f'session source headers conflict for session "{取字段(甲,"id")}"',
            'SESSION_QUERY_SOURCE_CONFLICT',
        )#抛出源冲突
