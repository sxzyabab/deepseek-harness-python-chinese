"""`sessionStats` 投影单元（对齐上游 session-stats/projection.ts）。"""
def 是否令牌增量(块):#流块是否携带非空首 token 增量
    """流块是否携带非空首 token 增量。"""
    类型=块.get('type') if isinstance(块,dict) else getattr(块,'type',None)#类型
    if 类型 in ('text-delta','reasoning-delta'):#文本增量
        文本=块.get('text') if isinstance(块,dict) else getattr(块,'text','')#文本
        return 文本!=''#非空
    if 类型=='tool-call-delta':#工具调用增量
        参数=块.get('argumentsDelta') if isinstance(块,dict) else getattr(块,'argumentsDelta','')#参数增量
        名称=块.get('name') if isinstance(块,dict) else getattr(块,'name',None)#名称
        return 参数!='' or 名称 is not None#非空
    return False#其它

def 用量输出令牌(用量):#从 usage 读 outputTokens
    """从 assistant/message usage 读 outputTokens。"""
    if not isinstance(用量,dict):#非记录
        return None#缺席
    值=用量.get('outputTokens')#字段
    if isinstance(值,(int,float)) and 值==值 and 值>=0:#有限非负
        return int(值)#整数
    return None#无效

def 统计初始():#折叠初始状态
    """折叠初始状态。"""
    return {'turns':0,'steps':0,'llmMs':0,'toolMs':0,'ttftMs':0,'ttftSteps':0,'decodeMs':0,'decodeTokens':0,'lastTurn':None,'openStep':None,'pendingCalls':{}}#初始

def 统计应用(状态,事件):#折叠一条事件
    """纯折叠 sessionStats。"""
    类型=事件.get('type') if isinstance(事件,dict) else getattr(事件,'type',None)#类型
    数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',{})#数据
    时刻=事件.get('time') if isinstance(事件,dict) else getattr(事件,'time',0)#时间
    if 类型=='step/start':#步骤开始
        return {**状态,'openStep':{'turn':数据['turn'],'step':数据['step'],'startTime':时刻,'firstTokenTime':None}}#打开步骤
    if 类型=='assistant/chunk':#流块
        开放=状态.get('openStep')#开放步骤
        if 开放 is None or 开放['turn']!=数据.get('turn') or 开放['step']!=数据.get('step'):#不匹配
            return 状态#原样
        if 开放.get('firstTokenTime') is not None or not 是否令牌增量(数据.get('chunk')):#已有首 token
            return 状态#原样
        return {**状态,'openStep':{**开放,'firstTokenTime':时刻}}#记下首 token
    if 类型=='assistant/message':#助手消息
        开放=状态.get('openStep')#开放步骤
        if 开放 is None or 开放['turn']!=数据.get('turn') or 开放['step']!=数据.get('step'):#不匹配
            return 状态#原样
        下一={**状态,'llmMs':状态['llmMs']+max(0,时刻-开放['startTime']),'openStep':None}#结算模型时间
        if 开放.get('firstTokenTime') is not None:#有首 token
            下一['ttftMs']=下一['ttftMs']+max(0,开放['firstTokenTime']-开放['startTime'])#TTFT
            下一['ttftSteps']=下一['ttftSteps']+1#计数
            输出=用量输出令牌(数据.get('usage'))#输出 token
            if 输出 is not None:#有 usage
                下一['decodeMs']=下一['decodeMs']+max(0,时刻-开放['firstTokenTime'])#解码时间
                下一['decodeTokens']=下一['decodeTokens']+输出#token 数
        return 下一#新状态
    if 类型=='tool/call':#工具调用
        待处理=dict(状态.get('pendingCalls') or {})#拷贝
        待处理[数据['callId']]=时刻#记下派发时刻
        return {**状态,'pendingCalls':待处理}#更新
    if 类型=='tool/result':#工具结果
        来源=数据.get('message',{}).get('source',{}) if isinstance(数据.get('message'),dict) else {}#来源
        调用标识=来源.get('callId')#callId
        待处理=状态.get('pendingCalls') or {}#待处理表
        if 调用标识 not in 待处理:#未匹配
            return 状态#原样
        新待处理={键:值 for 键,值 in 待处理.items() if 键!=调用标识}#去掉
        return {**状态,'toolMs':状态['toolMs']+max(0,时刻-待处理[调用标识]),'pendingCalls':新待处理}#结算
    if 类型=='step/end':#步骤结束
        return {**状态,'turns':状态['turns'] if 状态.get('lastTurn')==数据.get('turn') else 状态['turns']+1,'steps':状态['steps']+1,'lastTurn':数据.get('turn'),'openStep':None}#计数
    if 类型=='turn/end':#回合结束
        if len(状态.get('pendingCalls') or {})==0:#无遗留
            return 状态#原样
        return {**状态,'pendingCalls':{}}#清空遗留
    return 状态#其它事件

def 统计视图(状态):#wire 视图
    """公开视图是 totals 子集。"""
    return {'turns':状态['turns'],'steps':状态['steps'],'llmMs':状态['llmMs'],'toolMs':状态['toolMs'],'ttftMs':状态['ttftMs'],'ttftSteps':状态['ttftSteps'],'decodeMs':状态['decodeMs'],'decodeTokens':状态['decodeTokens']}#视图

会话统计投影定义={#注册表单元
    'key':'sessionStats',#键
    'stateVersion':1,#版本
    'stateSchema':None,#Python 侧不跑 zod
    'init':统计初始,#初始
    'apply':统计应用,#折叠
    'wire':{'viewSchema':None,'view':统计视图},#wire
}#定义结束
