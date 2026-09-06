"""会话日志里「本会话实际在跑哪个预设」的记录。

对齐上游 `agent-presets/src/session.ts`。公开面仅中文名。
"""
__all__=['解析会话预设']#仅中文公开名

def 解析会话预设(会话):
    """会话实际在跑的预设，最新一次选定胜出。请求头给出创建时值；之后每一次选定都是已记录事件。会话是对象，events 为事件 dict 元组，header 为 dict。"""
    事件列表=会话.events#事件日志
    下标=len(事件列表)-1#从最新往回
    while 下标>=0:#往回扫
        事件=事件列表[下标]#当前事件
        if 事件['type']=='agent-preset/selected':#选定事件
            载荷=事件['data']#事件载荷
            return 载荷['agentPreset'] if 'agentPreset' in 载荷 else None#胜出
        下标=下标-1#继续
    头=会话.header#创建头
    if 头 is None:#无头
        return None#无预设
    return 头['agentPreset'] if 'agentPreset' in 头 else None#回落到创建头
