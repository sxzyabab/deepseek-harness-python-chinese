"""压缩检查点出处：每个后端用于替换用户消息的关联来源构造器与类型，以及识别已持久化检查点的判断。"""

压缩检查点标记={'kind':'plugin','plugin':'compact'}#后端无关的检查点标记

def 压缩检查点来源(压缩事务标识,来源命令标识=None):
    """创建与一次压缩事务关联的检查点出处。"""
    出处={'kind':'plugin','plugin':'compact','compactionId':压缩事务标识}#插件标记加事务 id
    if 来源命令标识 is not None:#有命令 id 才写入
        出处['sourceCommandId']=来源命令标识#手动发起命令
    return 出处#出处对象

def 是否压缩检查点来源(出处):
    """测试已持久化的消息出处是否标识压缩检查点。"""
    if not isinstance(出处,dict):#非对象
        return False#不是
    if 'kind' not in 出处 or 'plugin' not in 出处:#缺标记
        return False#不是
    return 出处['kind']=='plugin' and 出处['plugin']==压缩检查点标记['plugin']#插件名匹配 compact

压缩检查点来源字段=('kind','plugin','compactionId','sourceCommandId')#具体压缩检查点所携带的消息出处字段
