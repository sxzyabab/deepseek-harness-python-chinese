"""已落定轮次页脚与 StatsLine 共用的延迟/吞吐折叠。

对齐上游 `ui-chat/src/client/contract/turn-metrics.ts`。公开面仅中文名。
"""

__all__=['用量输出令牌','助手步骤读数','推导回合指标']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 用量输出令牌(用量):#从用量取输出 token
    """非对象或缺席则 None。"""
    if 用量 is None:#空
        return None#无
    if isinstance(用量,dict):#映射
        值=用量.get('outputTokens')#键
    else:#对象
        值=getattr(用量,'outputTokens',None)#属性
    if isinstance(值,(int,float)) and 值==值 and 值>=0:#合法非负
        return 值#采纳
    return None#否则

def 助手步骤读数(节点):#读步骤指标
    """读一个 Assistant 节点的 TTFT、解码墙时与输出 token。"""
    时序=取字段(节点,'timing')#时序块
    ttftMs=None#缺
    decodeMs=None#缺
    if 时序 is not None:#有时序
        步起=取字段(时序,'stepStartTime')#步起
        首令=取字段(时序,'firstTokenTime')#首 token
        完成=取字段(时序,'completedTime')#完成
        if 步起 is not None and 首令 is not None:#完整 TTFT
            ttftMs=max(0,首令-步起)#首 token 差
        if 首令 is not None and 完成 is not None:#有解码
            decodeMs=max(0,完成-首令)#解码差
    return {'ttftMs':ttftMs,'decodeMs':decodeMs,'outputTokens':用量输出令牌(取字段(节点,'usage'))}#读数

def 推导回合指标(节点们):#折轮次指标
    """把 Assistant 节点折成每轮页脚指标。"""
    折叠={}#按轮累加
    for 节点 in 节点们:#遍历
        if 取字段(节点,'kind')!='assistant':#仅 Assistant
            continue#跳
        读=助手步骤读数(节点)#本步
        回合=取字段(节点,'turn')#轮
        步=取字段(节点,'step')#步
        折=折叠.get(回合)#累加器
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
        if 折['sampled'] and 折['decodeMs']>0:#带吞吐
            条['tokensPerSecond']=折['outputTokens']/(折['decodeMs']/1000)#吞吐
        if 'ttftMs' in 条 or 'tokensPerSecond' in 条:#有值
            指标[回合]=条#写
    return 指标#返回
