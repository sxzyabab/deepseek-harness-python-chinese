"""已结算回合页脚与统计行共用的延迟/吞吐折叠。

对齐上游 `ui-conversation/src/client/chat/turn-metrics.ts`。公开面仅中文名。
"""

__all__=['助手步骤读数','派生回合指标']#仅中文公开名

def 用量产出令牌(用量):#从未知 usage 取产出 token
    """非负有限数字才采纳。"""
    if not isinstance(用量,dict):#非映射
        return None#未记录
    值=用量.get('outputTokens')#产出
    if isinstance(值,(int,float)) and 值==值 and 值>=0:#有限非负
        return 值#采纳
    return None#未记录

def 助手步骤读数(节点):#读一步 TTFT/解码/产出
    """各部分未记录处为 None。"""
    计时=节点.get('timing') if isinstance(节点,dict) else getattr(节点,'timing',None)#计时
    步进=None if 计时 is None else (计时.get('stepStartTime') if isinstance(计时,dict) else getattr(计时,'stepStartTime',None))#步进
    首令牌=None if 计时 is None else (计时.get('firstTokenTime') if isinstance(计时,dict) else getattr(计时,'firstTokenTime',None))#首 token
    完成=None if 计时 is None else (计时.get('completedTime') if isinstance(计时,dict) else getattr(计时,'completedTime',None))#完成
    首令牌延迟=max(0,首令牌-步进) if 步进 is not None and 首令牌 is not None else None#TTFT
    解码=max(0,完成-首令牌) if 首令牌 is not None and 完成 is not None else None#解码墙钟
    用量=节点.get('usage') if isinstance(节点,dict) else getattr(节点,'usage',None)#用量
    return {'ttftMs':首令牌延迟,'decodeMs':解码,'outputTokens':用量产出令牌(用量)}#三读数

def 派生回合指标(节点们):#折叠助手节点为按回合页脚指标
    """TTFT 取最小步；吞吐=产出/解码秒。"""
    折叠表={}#回合→折叠
    for 节点 in 节点们:#遍历
        种=节点.get('kind') if isinstance(节点,dict) else getattr(节点,'kind',None)#kind
        if 种!='assistant':#非助手
            continue#跳过
        读数=助手步骤读数(节点)#本步
        回合=节点.get('turn') if isinstance(节点,dict) else getattr(节点,'turn',None)#回合号
        步=节点.get('step') if isinstance(节点,dict) else getattr(节点,'step',None)#步号
        折叠=折叠表.get(回合)#已有
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
        if 折叠['sampled'] and 折叠['decodeMs']>0:#有吞吐
            项['tokensPerSecond']=折叠['outputTokens']/(折叠['decodeMs']/1000)#吞吐
        if 'ttftMs' in 项 or 'tokensPerSecond' in 项:#至少一项
            指标[回合]=项#入表
    return 指标#映射
