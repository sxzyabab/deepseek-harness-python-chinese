from .卡片表单 import 卡片表单,数字字段#卡片表单

__all__=['子智能体限额卡片控制器','子智能体卡片外壳','子智能体卡片面']#仅中文公开名

def 限额字段(字段,下限):
    """数字字段加下限与安全整数校验。"""
    数值=数字字段(字段)#基础
    def 解析(文本):
        """解析并校验下限。"""
        写=数值['parse'](文本)#先数字
        if 写 is None or 写.get('kind')!='set':#非 set
            return 写#原样
        值=写['value']#数值
        if type(值) is bool:#布尔不是数
            return None#拒
        if type(值) is not int or 值<下限:#非法
            return None#拒
        return 写#合法
    规格=dict(数值)#拷
    规格['parse']=解析#覆盖
    return 规格#规格

class 子智能体限额卡片控制器:#限额卡
    """Host subagent 分区上的暂存委托限额。"""
    def __init__(自身,作用域):
        """绑两字段。"""
        自身.表单=卡片表单(作用域,[限额字段('maxDepth',0),限额字段('maxActiveSubagents',1)])#表单
        def 投影():
            """外壳加两字段。"""
            壳=自身.表单.外壳()#外壳
            壳['maxDepth']=自身.表单.字段('maxDepth')#深度
            壳['maxActiveSubagents']=自身.表单.字段('maxActiveSubagents')#活动数
            return 壳#态
        自身.仓=自身.表单.绑定(投影)#快照

    def 注入(自身):
        """槽渲染器面。"""
        面=dict(自身.表单.动作())#动作
        面['hooks']={'subagentLimitsCard':自身.仓}#钩子
        return 面#面

def 子智能体卡片外壳(限额,模型):
    """两分区聚合外壳。"""
    区=[]#可用
    if 限额.get('available'):#限额可用
        区.append(限额)#收
    if 模型.get('available'):#模型可用
        区.append(模型)#收
    return {#外壳
        'available':len(区)>0,#任一
        'writable':all(段.get('writable') for 段 in 区),#皆可写
        'dirty':any(段.get('dirty') for 段 in 区),#任一脏
        'invalid':any(段.get('invalid') for 段 in 区) or (模型.get('available') and 模型.get('dirty') and 模型.get('conflicted')),#非法或冲突
        'saving':any(段.get('saving') for 段 in 区),#保存中
        'failed':any(段.get('failed') for 段 in 区),#失败
    }#结束

def 子智能体卡片面(限额面,模型面):
    """合成共用保存/丢弃。"""
    def 保存():
        """经各自命名空间保存。"""
        限额态=限额面['hooks']['subagentLimitsCard'].getSnapshot()#限额
        模型态=模型面['hooks']['subagentModelSelectionCard'].getSnapshot()#模型
        壳=子智能体卡片外壳(限额态,模型态)#壳
        if not 壳['available'] or not 壳['writable'] or not 壳['dirty'] or 壳['invalid'] or 壳['saving']:#不可
            return#停
        if 模型态.get('available') and 模型态.get('dirty'):#模型脏
            模型面['save']()#存
        if 限额态.get('available') and 限额态.get('dirty'):#限额脏
            限额面['save']()#存
    def 丢弃():
        """保存中不丢。"""
        壳=子智能体卡片外壳(限额面['hooks']['subagentLimitsCard'].getSnapshot(),模型面['hooks']['subagentModelSelectionCard'].getSnapshot())#壳
        if 壳['saving']:#保存中
            return#停
        限额面['discard']()#丢限额
        模型面['discard']()#丢模型
    钩子=dict(限额面['hooks'])#拷
    钩子.update(模型面['hooks'])#合并
    return {#面
        'hooks':钩子,#钩子
        'editLimit':限额面['edit'],#改限额
        'resetLimit':限额面['resetField'],#重置
        'toggleEnabled':模型面['toggleEnabled'],#开关启用
        'toggleModel':模型面['toggleModel'],#开关模型
        'retryCatalog':模型面['retryCatalog'],#重试
        'save':保存,#保存
        'discard':丢弃,#丢弃
    }#结束
