__all__=['助手步骤读数']


def 助手步骤读数(节点):
    '一个已结算助手节点的首 token 延迟、解码墙钟和输出 token。没记下的部分是 None'
    时机=节点.get('timing')
    首延迟=None
    解码=None
    if isinstance(时机,dict) and 时机.get('stepStartTime') is not None and 时机.get('firstTokenTime') is not None:
        首延迟=时机['firstTokenTime']-时机['stepStartTime']
        if 首延迟<0:
            首延迟=0
    if isinstance(时机,dict) and 时机.get('firstTokenTime') is not None:
        解码=时机['completedTime']-时机['firstTokenTime']
        if 解码<0:
            解码=0
    用量=节点.get('usage')
    输出=None
    if isinstance(用量,dict):
        值=用量.get('outputTokens')
        if isinstance(值,(int,float)) and not isinstance(值,bool) and 值==值 and 值>=0:
            输出=值
    return {'ttftMs':首延迟,'decodeMs':解码,'outputTokens':输出}
