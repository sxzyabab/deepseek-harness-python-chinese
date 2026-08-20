"""整帧 Cordis 面板直接使用的宿主操作接缝。

对齐上游 `ui-cordis/src/client/dynamic-port.ts`。公开面仅中文名。
"""

__all__=['动作结果成功','动作结果失败','端口动词','清单行说明','规范化动作结果']#仅中文公开名

动作结果成功={'ok':True}#成功形

端口动词=('stop','remove','inventory')#CordisDynamicPort 动词

清单行说明='与 Remote 清单行同形；面板按 agentId/pluginId/packages/activeRun/latestRun 消费。'#行说明

def 动作结果失败(消息):#失败形
    """带消息失败。"""
    return {'ok':False,'message':消息}#败

def 规范化动作结果(值):#折成动作结果
    """成功或带消息失败。"""
    if 值 is True or (isinstance(值,dict) and 值.get('ok') is True):#成功
        return {'ok':True}#成
    if isinstance(值,dict):#映射
        return {'ok':False,'message':str(值.get('message') or 'operation failed')}#败
    return {'ok':False,'message':str(值)}#败
