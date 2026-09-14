
__all__=['插件事件帧','事件端点','热更新错误']#仅中文公开名

事件端点='/plugins/events'#推送 graph/rebuilt 帧的系统 SSE 端点

class 热更新错误(Exception):
    """本包异常基类。"""

class 插件事件帧(dict):#SSE 帧映射形状
    """一帧 SSE：连接时的整图，或一条打包重建通知。键：type；graph 帧另有 graph；rebuilt 帧另有 id、rev。"""
