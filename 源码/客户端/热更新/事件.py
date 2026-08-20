"""`/plugins/events` 开发 SSE 通道的线协议 — 本包两半边的单一来源。

对齐上游 `hmr/src/events.ts`。公开面仅中文名；路径与帧判别标签英文字面量保持上游。
"""

__all__=['插件事件帧','事件端点']#仅中文公开名

事件端点='/plugins/events'#推送 graph/rebuilt 帧的系统 SSE 端点

class 插件事件帧(dict):#SSE 帧映射形状
    """一帧 SSE：连接时的整图，或一条打包重建通知。键：type；graph 帧另有 graph；rebuilt 帧另有 id、rev。"""
