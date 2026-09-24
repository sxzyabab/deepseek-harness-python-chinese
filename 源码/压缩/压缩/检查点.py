"""压缩检查点出处：每个后端用于替换用户消息的关联来源构造器与类型，以及识别已持久化检查点的判断。"""

压缩检查点标记={'kind':'compact-checkpoint'}

def 压缩检查点来源(压缩事务标识,来源命令标识=None):
    """创建与一次压缩事务关联的检查点出处。"""
    出处={'kind':'compact-checkpoint','compactionId':压缩事务标识}
    if 来源命令标识 is not None:
        出处['sourceCommandId']=来源命令标识
    return 出处

def 是否压缩检查点来源(出处):
    """测试已持久化的消息出处是否标识压缩检查点。"""
    if not isinstance(出处,dict):
        return False
    return ('kind' in 出处) and 出处['kind']=='compact-checkpoint'

压缩检查点来源字段=('kind','compactionId','sourceCommandId')
