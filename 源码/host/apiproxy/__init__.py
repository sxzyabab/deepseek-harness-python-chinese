"""宿主 API 网关包根：浏览器安全子路径再导出。对齐上游 `host/apiproxy/src/index.ts` 客户端可用面。"""

from .fetch处理 import 转fetch处理#宿主侧 fetch 处理器

__all__=['转fetch处理','toFetchHandler']#公开面

toFetchHandler=转fetch处理#上游名
