"""子智能体引用：只读编写器认领判定。

对齐上游 `ui-subagent/src/client/index.ts` 中的 `selectReadOnlySubagent`。
公开面仅中文名。只读撰写器见 `只读撰写器.py`；目录动作 React 半仍欠。
"""

__all__=['选择只读子智能体']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 选择只读子智能体(属主):#是否改用只读编写器
    """一次性历史或续跑属主不可用时认领编写器。"""
    会话=取字段(属主,'session')#会话
    子=取字段(会话,'subagent')#本会话的子智能体元数据
    if 子 is None:#不是子智能体会话
        return None#不认领
    地址=取字段(子,'address')#地址
    if 取字段(地址,'mode')=='one-shot':#一次性
        return {'reason':'one-shot'}#只读历史
    if 取字段(子,'parentAvailable'):#父会话在
        return None#继续用默认编写器
    if 取字段(会话,'running') is True:#运行中不抢
        return None#保留默认编写器
    return {'reason':'parent-unavailable'}#父不可用接管
