"""子智能体身份（模式/标签）与活动回合时长的纯会话投影。"""
from .描述符 import 折叠子智能体描述符,子智能体描述符错误#导入描述符折叠

def 计时初始():
    """计时折叠初始状态。"""
    return {'descriptorSeen':False,'settledMs':0}#初始未见描述符

def 计时应用(状态,事件):
    """围绕子体自身耐久描述符折叠回合边界。状态与事件为 dict。"""
    类型=事件['type'] if 'type' in 事件 else None#事件类型
    时刻=事件['time'] if 'time' in 事件 else None#事件时间
    if 类型=='turn/start':#回合开始
        if 'descriptorSeen' in 状态 and 状态['descriptorSeen']:#描述符后才算活动
            下一=dict(状态)#复制
            下一['active']={'since':时刻,'through':时刻}#打开活动区间
            return 下一#新状态
        下一=dict(状态)#复制
        下一['pendingTurnStart']=时刻#描述符前只记下待提升起点
        return 下一#新状态
    if 类型=='subagent/descriptor':#描述符到达
        活动起点=None#进行中或待提升起点
        if 'active' in 状态 and 状态['active'] is not None:#有开放区间
            活动=状态['active']#活动区间
            活动起点=活动['since'] if 'since' in 活动 else None#进行中起点
        elif 'pendingTurnStart' in 状态:#有待提升
            活动起点=状态['pendingTurnStart']#待提升起点
        下一={'descriptorSeen':True,'settledMs':0}#重置为子体权威原点
        if 活动起点 is not None:#有开放回合
            下一['active']={'since':活动起点,'through':时刻}#把开放区间接到描述符时刻
        return 下一#新状态
    if 类型=='turn/end':#回合结束
        if 'descriptorSeen' not in 状态 or not 状态['descriptorSeen']:#描述符前的结束
            if 'pendingTurnStart' not in 状态:#没有待提升起点
                return 状态#原样
            下一=dict(状态)#复制
            下一.pop('pendingTurnStart',None)#丢掉已关闭的待提升
            return 下一#其余原样
        if 'active' not in 状态 or 状态['active'] is None:#没有开放区间
            return 状态#原样
        活动=状态['active']#拆出活动区间
        下一={键:值 for 键,值 in 状态.items() if 键!='active'}#其余状态
        已结算=状态['settledMs'] if 'settledMs' in 状态 else 0#已结算
        下一['settledMs']=已结算+max(0,时刻-活动['since'])#加上非负时长
        return 下一#新状态
    if 'active' not in 状态 or 状态['active'] is None:#无开放区间则忽略
        return 状态#原样
    下一=dict(状态)#复制
    下一['active']=dict(状态['active'])#复制活动
    下一['active']['through']=时刻#把截止推到本事件
    return 下一#新状态

def 计时视图(状态):
    """计时投影公开视图。状态为 dict。省略无开放区间的 active 键。"""
    已结算=状态['settledMs'] if 'settledMs' in 状态 else 0#已结算毫秒
    视图={'settledMs':已结算}#已结算毫秒
    if 'active' in 状态 and 状态['active'] is not None:#有开放区间才带上
        视图['active']=状态['active']#带上
    return 视图#公开视图

子智能体计时投影定义={#计时投影定义
    'key':'subagentTiming',#投影键
    'schema':None,#公开视图模式（Python侧不做zod校验）
    'init':计时初始,#初始未见描述符
    'apply':计时应用,#折叠一条事件
    'view':计时视图,#投影公开视图
    'stateVersion':2,#状态版本
}#subagentTimingProjectionDefinition结束

def 描述符身份(事件):
    """解释一条 subagent/descriptor 事件的身份；载荷不可信时无值。事件为 dict。"""
    try:
        描述符=折叠子智能体描述符([事件])#解析描述符
    except 子智能体描述符错误:
        描述符=None#当作无值
    if 描述符 is None:#无法信任
        return None#无值
    序号=事件['seq'] if 'seq' in 事件 else None#事件序号
    if 'mode' in 描述符 and 描述符['mode']=='one-shot':#一次性身份
        身份={'mode':'one-shot','seq':序号}#一次性
        if 'label' in 描述符:#有标签才展开
            身份['label']=描述符['label']#展开
        return 身份#一次性
    return {'mode':'continuable','label':描述符['label'],'seq':序号}#可续跑身份

def 身份初始():
    """身份折叠初始状态。"""
    return {}#初始无身份

def 身份应用(状态,事件):
    """从 subagent/descriptor 事件后写折叠耐久模式/标签身份。状态与事件为 dict。"""
    if 'type' not in 事件 or 事件['type']!='subagent/descriptor':#非描述符忽略
        return 状态#原样
    身份=描述符身份(事件)#解释身份
    if 身份 is None:#非法则清空
        return {}#清空
    return {'identity':身份}#合法则后写

def 身份视图(状态):
    """无身份则 None。状态为 dict。"""
    if 'identity' in 状态:#有身份
        return 状态['identity']#身份
    return None#无身份

子智能体身份投影定义={#身份投影定义
    'key':'subagent',#投影键
    'schema':None,#公开视图模式
    'init':身份初始,#初始无身份
    'apply':身份应用,#折叠一条事件
    'view':身份视图,#无身份则null哨兵
    'stateVersion':2,#状态版本
}#subagentIdentityProjectionDefinition结束
