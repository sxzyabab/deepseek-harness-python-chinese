"""封闭运行时 JSON-RPC 智能体二进制。裸插件从已安装运行时闭包解析，相对插件仍相对配置。

对齐上游 `示例/jsonrpc-demo/src/packaged-bin.ts`。公开面仅中文名。
"""
from .运行器 import 运行JSONRPC智能体#共享进程生命周期

运行JSONRPC智能体(__file__)#以本入口路径为裸插件解析基
