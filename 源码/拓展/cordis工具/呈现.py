__all__=['巡检错误','呈现列表调用','呈现查询调用']

class 巡检错误(Exception):
    """Cordis 巡检失败。"""

def 呈现列表调用():
    """提供方目录巡检的可回放通用调用卡片。"""
    return {'card':'generic','kind':'read','title':'List Cordis Inspect Providers'}

def 呈现查询调用(参数):
    """一次提供方查询的可回放通用调用卡片。"""
    return {'card':'generic','kind':'read','title':'Query Cordis '+参数['platform']+' '+参数['provider']+'.'+参数['method']}
