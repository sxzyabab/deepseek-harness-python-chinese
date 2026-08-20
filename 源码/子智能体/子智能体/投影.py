"""子智能体身份（模式/标签）与活动回合时长的纯会话投影。"""
from .描述符 import 折叠子智能体描述符#导入描述符折叠

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 计时初始():#初始未见描述符
    """计时折叠初始状态。"""
    return {'descriptorSeen':False,'settledMs':0}#初始未见描述符

def 计时应用(状态,事件):#折叠一条计时事件
    """围绕子体自身耐久描述符折叠回合边界。"""
    类型=取字段(事件,'type')#事件类型
    时刻=取字段(事件,'time')#事件时间
    if 类型=='turn/start':#回合开始
        if 状态.get('descriptorSeen'):#描述符后才算活动
            下一=dict(状态)#复制
            下一['active']={'since':时刻,'through':时刻}#打开活动区间
            return 下一#新状态
        下一=dict(状态)#复制
        下一['pendingTurnStart']=时刻#描述符前只记下待提升起点
        return 下一#新状态
    if 类型=='subagent/descriptor':#描述符到达
        活动起点=None#进行中或待提升起点
        if 状态.get('active') is not None:#有开放区间
            活动起点=状态['active'].get('since')#进行中起点
        elif 'pendingTurnStart' in 状态:#有待提升
            活动起点=状态.get('pendingTurnStart')#待提升起点
        下一={'descriptorSeen':True,'settledMs':0}#重置为子体权威原点
        if 活动起点 is not None:#有开放回合
            下一['active']={'since':活动起点,'through':时刻}#把开放区间接到描述符时刻
        return 下一#新状态
    if 类型=='turn/end':#回合结束
        if not 状态.get('descriptorSeen'):#描述符前的结束
            if 'pendingTurnStart' not in 状态:#没有待提升起点
                return 状态#原样
            下一=dict(状态)#复制
            下一.pop('pendingTurnStart',None)#丢掉已关闭的待提升
            return 下一#其余原样
        if 状态.get('active') is None:#没有开放区间
            return 状态#原样
        活动=状态['active']#拆出活动区间
        下一={键:值 for 键,值 in 状态.items() if 键!='active'}#其余状态
        下一['settledMs']=状态.get('settledMs',0)+max(0,时刻-活动['since'])#加上非负时长
        return 下一#新状态
    if 状态.get('active') is None:#无开放区间则忽略
        return 状态#原样
    下一=dict(状态)#复制
    下一['active']=dict(状态['active'])#复制活动
    下一['active']['through']=时刻#把截止推到本事件
    return 下一#新状态

def 计时视图(状态):#投影公开视图
    """计时投影公开视图。"""
    视图={'settledMs':状态.get('settledMs',0)}#已结算毫秒
    if 状态.get('active') is not None:#有开放区间才带上
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

def 描述符身份(事件):#从事件取身份
    """解释一条 subagent/descriptor 事件的身份；载荷不可信时无值。"""
    try:#折叠单事件
        描述符=折叠子智能体描述符([事件])#解析描述符
    except Exception:#畸形当前版本载荷会抛
        # 投影折叠绝不能抛，因此损坏折成无值。
        描述符=None#当作无值
    if 描述符 is None:#无法信任
        return None#无值
    序号=取字段(事件,'seq')#事件序号
    if 描述符.get('mode')=='one-shot':#一次性身份
        身份={'mode':'one-shot','seq':序号}#一次性
        if 'label' in 描述符:#有标签才展开
            身份['label']=描述符['label']#展开
        return 身份#一次性
    return {'mode':'continuable','label':描述符['label'],'seq':序号}#可续跑身份

def 身份初始():#初始无身份
    """身份折叠初始状态。"""
    return {}#初始无身份

def 身份应用(状态,事件):#折叠一条身份事件
    """从 subagent/descriptor 事件后写折叠耐久模式/标签身份。"""
    if 取字段(事件,'type')!='subagent/descriptor':#非描述符忽略
        return 状态#原样
    身份=描述符身份(事件)#解释身份
    if 身份 is None:#非法则清空
        return {}#清空
    return {'identity':身份}#合法则后写

def 身份视图(状态):#身份公开视图
    """无身份则 null 哨兵。"""
    return 状态.get('identity')#无身份则None（对齐null哨兵）

子智能体身份投影定义={#身份投影定义
    'key':'subagent',#投影键
    'schema':None,#公开视图模式
    'init':身份初始,#初始无身份
    'apply':身份应用,#折叠一条事件
    'view':身份视图,#无身份则null哨兵
    # 身份获得 seq 字段时上调：更旧的检查点行会回放到模式拒绝的值，因此必须再折叠。
    'stateVersion':2,#状态版本
}#subagentIdentityProjectionDefinition结束
