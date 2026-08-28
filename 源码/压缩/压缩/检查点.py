"""压缩检查点出处：每个后端用于替换用户消息的关联来源构造器与类型，以及识别已持久化检查点的判断。

seam 本身在包根，由它再导出这些约定；本模块是纯类型/值/判断出口（无 cordis 导入、无模块扩充），以便客户端与 wire 程序无需加载宿主插件的 Context 合并即可命名检查点来源。
"""

压缩检查点标记={'kind':'plugin','plugin':'compact'}#后端无关的检查点标记，对齐 Object.freeze

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 压缩检查点来源(压缩事务标识,来源命令标识=None):#构造检查点来源
    """创建与一次压缩事务关联的检查点出处。compactionId 为所属压缩身份；sourceCommandId 为发起的手动命令（若有）。返回不可变检查点来源。"""
    出处={'kind':'plugin','plugin':'compact','compactionId':压缩事务标识}#插件标记加事务 id
    if 来源命令标识 is not None:#有命令 id 才写入
        出处['sourceCommandId']=来源命令标识#手动发起命令
    return 出处#语义上冻结的出处对象

def 是否压缩检查点来源(出处):#是否压缩检查点
    """测试已持久化的消息出处是否标识压缩检查点。出处从表面用户消息恢复；返回是否携带与后端无关的检查点标记。"""
    return 取字段(出处,'kind')=='plugin' and 取字段(出处,'plugin')==压缩检查点标记['plugin']#插件名匹配 compact

压缩检查点来源字段=('kind','plugin','compactionId','sourceCommandId')#具体压缩检查点所携带的消息出处字段
