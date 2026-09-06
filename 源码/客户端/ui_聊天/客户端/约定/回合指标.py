"""已落定轮次页脚与 StatsLine 共用的延迟/吞吐折叠。

对齐上游 `ui-chat/src/client/contract/turn-metrics.ts`。公开面仅中文名。
节点与用量为快照 dict。
"""

__all__=['用量输出令牌','助手步骤读数','推导回合指标']#仅中文公开名

def 用量输出令牌(用量):
    """从用量取输出 token。用量为 dict。"""
    if 用量 is None:#空
        return None#无
    if 'outputTokens' not in 用量:#缺席
        return None#无
    值=用量['outputTokens']#键
    if isinstance(值,bool):#bool 不是计数
        return None#否则
    if isinstance(值,(int,float)) and 值==值 and 值>=0:#合法非负
        return 值#采纳
    return None#否则

def 助手步骤读数(节点):
    """读一个 Assistant 节点的 TTFT、解码墙时与输出 token。节点为 dict。"""
    时序=节点['timing'] if 'timing' in 节点 else None#时序块
    ttftMs=None#缺
    decodeMs=None#缺
    if 时序 is not None:#有时序
        步起=时序['stepStartTime'] if 'stepStartTime' in 时序 else None#步起
        首令=时序['firstTokenTime'] if 'firstTokenTime' in 时序 else None#首 token
        完成=时序['completedTime'] if 'completedTime' in 时序 else None#完成
        if 步起 is not None and 首令 is not None:#完整 TTFT
            ttftMs=max(0,首令-步起)#首 token 差
        if 首令 is not None and 完成 is not None:#有解码
            decodeMs=max(0,完成-首令)#解码差
    用量=节点['usage'] if 'usage' in 节点 else None#用量
    return {'ttftMs':ttftMs,'decodeMs':decodeMs,'outputTokens':用量输出令牌(用量)}#读数

def 推导回合指标(节点列表):
    """把 Assistant 节点折成每轮页脚指标。"""
    折叠={}#按轮累加
    for 节点 in 节点列表:#遍历
        if ('kind' not in 节点) or 节点['kind']!='assistant':#仅 Assistant
            continue#跳
        读=助手步骤读数(节点)#本步
        回合=节点['turn'] if 'turn' in 节点 else None#轮
        步=节点['step'] if 'step' in 节点 else None#步
        折=折叠[回合] if 回合 in 折叠 else None#累加器
        if 折 is None:#新轮
            折={'firstStep':步,'firstStepTtftMs':读['ttftMs'],'decodeMs':0,'outputTokens':0,'sampled':False}#初
            折叠[回合]=折#写
        elif 步 is not None and 步<折['firstStep']:#更早步骤
            折['firstStep']=步#更新
            折['firstStepTtftMs']=读['ttftMs']#更新 TTFT
        if 读['decodeMs'] is not None and 读['outputTokens'] is not None:#成对样本
            折['decodeMs']+=读['decodeMs']#累加解码
            折['outputTokens']+=读['outputTokens']#累加输出
            折['sampled']=True#已采样
    指标={}#输出表
    for 回合,折 in 折叠.items():#逐轮
        条={}#本轮
        if 折['firstStepTtftMs'] is not None:#带 TTFT
            条['ttftMs']=折['firstStepTtftMs']#写
        if 折['sampled'] is True and 折['decodeMs']>0:#带吞吐
            条['tokensPerSecond']=折['outputTokens']/(折['decodeMs']/1000)#吞吐
        if 'ttftMs' in 条 or 'tokensPerSecond' in 条:#有值
            指标[回合]=条#写
    return 指标#返回
