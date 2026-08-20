"""/api URL 前缀 — web 传输两半边的单一来源。

对齐上游 `connection/src/api-path.ts`。公开面仅中文名。node 半边在 web 服务器上登记此外缀；两半边共用事件路径给浏览器 WebSocket 下行。
"""

__all__=['接口路径','复用事件路径','宿主事件路径']#仅中文公开名

接口路径='/api'##/api 前缀
复用事件路径=接口路径+'/events.mux'#复用事件下行
宿主事件路径=接口路径+'/events.host'#宿主事件下行
