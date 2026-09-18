"""只读运行时巡检的可回放渲染意图。"""

__all__=['呈现巡检列表调用','呈现巡检查询调用']#仅中文公开名

def 呈现巡检列表调用():
    """渲染提供方目录巡检。"""
    return {'card':'generic','kind':'read','title':'List Cordis Inspect Providers'}#通用只读卡片

def 呈现巡检查询调用(参数):
    """渲染一次提供方查询。参数为 dict。"""
    return {'card':'generic','kind':'read','title':'Query Cordis '+参数['platform']+' '+参数['provider']+'.'+参数['method']}#通用只读卡片
