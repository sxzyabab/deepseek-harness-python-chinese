from ..异常 import 页面失败文案

__all__=['动作结果成功','动作结果失败','端口动词','清单行说明','规范化动作结果']#仅中文公开名

动作结果成功={'ok':True}

端口动词=('stop','remove','inventory')#CordisDynamicPort 动词

清单行说明='与 Remote 清单行同形；面板按 agentId/pluginId/packages/activeRun/latestRun 消费。'

def 动作结果失败(消息):
    '带消息失败'
    if isinstance(消息,(str,BaseException)) and 消息!='':
        return {'ok':False,'message':页面失败文案(消息)}
    return {'ok':False,'message':消息}

def 规范化动作结果(值):
    '成功或带消息失败'
    if 值 is True or (isinstance(值,dict) and 值.get('ok') is True):
        return {'ok':True}
    if isinstance(值,dict):
        return {'ok':False,'message':页面失败文案(值.get('message') or 'operation failed')}
    return {'ok':False,'message':页面失败文案(值)}
