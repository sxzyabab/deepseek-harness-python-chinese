
__all__=['助手步骤读数','派生回合指标']#仅中文公开名

def 用量产出令牌(用量):
    """从用量取产出 token。用量为 dict。"""
    if 用量 is None:#空
        return None#未记录
    if 'outputTokens' not in 用量:#缺席
        return None#未记录
    值=用量['outputTokens']#产出
    if isinstance(值,bool):#bool 不是计数
        return None#未记录
    if isinstance(值,(int,float)) and 值==值 and 值>=0:#有限非负
        return 值#采纳
    return None#未记录

def 助手步骤读数(节点):
    """读一步 TTFT、解码墙时与产出 token。节点为 dict。"""
    计时=节点['timing'] if 'timing' in 节点 else None#计时
    首令牌延迟=None#缺
    解码=None#缺
    if 计时 is not None:#有计时
        步进=计时['stepStartTime'] if 'stepStartTime' in 计时 else None#步进
        首令牌=计时['firstTokenTime'] if 'firstTokenTime' in 计时 else None#首 token
        完成=计时['completedTime'] if 'completedTime' in 计时 else None#完成
        if 步进 is not None and 首令牌 is not None:#完整 TTFT
            首令牌延迟=max(0,首令牌-步进)#TTFT
        if 首令牌 is not None and 完成 is not None:#有解码
            解码=max(0,完成-首令牌)#解码墙钟
    用量=节点['usage'] if 'usage' in 节点 else None#用量
    return {'ttftMs':首令牌延迟,'decodeMs':解码,'outputTokens':用量产出令牌(用量)}#三读数

def 派生回合指标(节点列表):
    """TTFT 取最小步；吞吐=产出/解码秒。节点列表为 dict 列表。"""
    折叠表={}#回合→折叠
    for 节点 in 节点列表:#遍历
        if ('kind' not in 节点) or 节点['kind']!='assistant':#非助手
            continue#跳过
        读数=助手步骤读数(节点)#本步
        回合=节点['turn'] if 'turn' in 节点 else None#回合号
        步=节点['step'] if 'step' in 节点 else None#步号
        折叠=折叠表[回合] if 回合 in 折叠表 else None#已有
        if 折叠 is None:#新建
            折叠={'firstStep':步,'firstStepTtftMs':读数['ttftMs'],'decodeMs':0,'outputTokens':0,'sampled':False}#初值
            折叠表[回合]=折叠#入表
        elif 步 is not None and 步<折叠['firstStep']:#更早步
            折叠['firstStep']=步#改步号
            折叠['firstStepTtftMs']=读数['ttftMs']#改 TTFT
        if 读数['decodeMs'] is not None and 读数['outputTokens'] is not None:#可算吞吐
            折叠['decodeMs']+=读数['decodeMs']#累加解码
            折叠['outputTokens']+=读数['outputTokens']#累加产出
            折叠['sampled']=True#有样本
    指标={}#回合→指标
    for 回合,折叠 in 折叠表.items():#写出
        项={}#空
        if 折叠['firstStepTtftMs'] is not None:#有 TTFT
            项['ttftMs']=折叠['firstStepTtftMs']#写入
        if 折叠['sampled'] is True and 折叠['decodeMs']>0:#有吞吐
            项['tokensPerSecond']=折叠['outputTokens']/(折叠['decodeMs']/1000)#吞吐
        if 'ttftMs' in 项 or 'tokensPerSecond' in 项:#至少一项
            指标[回合]=项#入表
    return 指标#映射
