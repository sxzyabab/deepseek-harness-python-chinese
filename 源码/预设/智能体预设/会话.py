"""会话日志里「本会话实际在跑哪个预设」的记录。

对齐上游 `agent-presets/src/session.ts`。公开面仅中文名。
"""
__all__=['解析会话预设']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 解析会话预设(会话):#解析会话实际预设
    """会话实际在跑的预设，最新一次选定胜出。请求头给出创建时值；之后每一次选定都是已记录事件。"""
    事件们=取字段(会话,'events') or []#事件日志
    下标=len(事件们)-1#从最新往回
    while 下标>=0:#往回扫
        事件=事件们[下标]#当前事件
        if 取字段(事件,'type')=='agent-preset/selected':#选定事件
            return 取字段(取字段(事件,'data'),'agentPreset')#胜出
        下标=下标-1#继续
    头=取字段(会话,'header')#创建头
    return 取字段(头,'agentPreset')#回落到创建头
