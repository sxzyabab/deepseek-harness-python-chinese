"""通用 JSON-RPC 智能体二进制。外部配置拥有其裸插件包；打包运行时改走打包二进制。

对齐上游 `示例/jsonrpc-demo/src/bin.ts`。公开面仅中文名。
"""
from .运行器 import 运行JSONRPC智能体#共享进程生命周期

运行JSONRPC智能体()#启动通用入口，配置项目自有插件包
