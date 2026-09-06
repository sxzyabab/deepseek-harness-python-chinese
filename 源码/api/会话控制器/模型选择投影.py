"""持久模型选择意图与请求使用投影。

对齐上游 `session-controller/src/model-selection-projection.ts`。公开面仅中文名。
"""
__all__=['安装模型选择投影']#仅中文公开名

def 选择相同(左,右):
    """两条模型选择是否相同。左、右为 dict 或 None。"""
    if 左 is 右:#同引用
        return True#相同
    if 左 is None or 右 is None:#一方为空
        return False#不同
    左力度=左['reasoningEffort'] if 'reasoningEffort' in 左 else None#左力度
    右力度=右['reasoningEffort'] if 'reasoningEffort' in 右 else None#右力度
    return 左['provider']==右['provider'] and 左['model']==右['model'] and 左力度==右力度#字段

def 应用模型选择投影(状态,事件):
    """按事件推进 durable modelSelection 状态。状态与事件为 dict。"""
    种类=事件['type']#事件类型
    if 种类=='model/selection':#用户选择
        数据=事件['data']#载荷
        待定=状态['pending'] if 'pending' in 状态 else None#pending
        if 选择相同(待定,数据):#未变
            return 状态#原样
        return {'lastUsed':状态['lastUsed'] if 'lastUsed' in 状态 else None,'pending':数据}#更新 pending
    if 种类!='request/header':#其它
        return 状态#不变
    头=事件['data']['header']#请求头
    配置=头['config']#配置
    最近使用={'provider':配置['provider'],'model':配置['model']}#lastUsed
    if 'reasoningEffort' in 配置 and 配置['reasoningEffort'] is not None:#有推理
        最近使用['reasoningEffort']=str(配置['reasoningEffort'])#推理
    待定=状态['pending'] if 'pending' in 状态 else None#原 pending
    待定=None if 选择相同(待定,最近使用) else 待定#消费 pending
    已用=状态['lastUsed'] if 'lastUsed' in 状态 else None#原 lastUsed
    原待定=状态['pending'] if 'pending' in 状态 else None#比较用
    if 选择相同(已用,最近使用) and 待定 is 原待定:#未变
        return 状态#原样
    return {'lastUsed':最近使用,'pending':待定}#新状态

def 初值模型选择():
    """投影初值。"""
    return {'lastUsed':None,'pending':None}#初值

def 视图模型选择(状态):
    """线上视图：next 回退 pending 否则 lastUsed。状态为 dict。"""
    待定=状态['pending'] if 'pending' in 状态 else None#pending
    已用=状态['lastUsed'] if 'lastUsed' in 状态 else None#lastUsed
    return {'lastUsed':已用,'next':待定 if 待定 is not None else 已用}#next 回退

def 安装模型选择投影(上下文):
    """在 sessionProjections 注册 modelSelection 列。"""
    上下文.sessionProjections.register({#注册定义
        'key':'modelSelection',#键
        'init':初值模型选择,#初值
        'apply':应用模型选择投影,#折叠
        'wire':{'view':视图模型选择},#线上视图
        'stateVersion':2,#版本
    })#register 结束
