"""LSP 缝词汇表：归一化的请求、提供方与结果约定。

对齐上游 `lsp/src/types.ts`。公开面仅中文名。仅词汇——语言服务器错误分类与语言服务器提供方标识品牌工厂是运行时，放在包根。位置与范围是零基 UTF-16，与协议一致；面向模型的工具拥有一基光标约定。本缝不暴露协议类型、进程或文档控制，也不暴露通用 JSON-RPC 逃生口——只有四种语义操作。字段键与操作字面量保持上游 wire 名。
"""
from .品牌 import 语言服务器提供方标识#再导出提供方 id 品牌

__all__=[#仅中文公开名
    '语言服务器提供方标识','语言服务器操作','语言服务器位置字段','语言服务器范围字段',
    '语言服务器查询请求字段','语言服务器提供方查询字段','语言服务器定位字段',
    '语言服务器悬停字段','语言服务器查询结果种类','语言服务器提供方字段','语言服务器服务字段',
]#公开面结束

语言服务器操作=('goToDefinition','findReferences','goToImplementation','hover')#四种语义操作；封闭联合
语言服务器位置字段=('line','character')#零基 UTF-16 光标：行与列
语言服务器范围字段=('start','end')#零基 UTF-16 半开范围 [start, end)
语言服务器查询请求字段=('operation','filePath','position','workspaceRoot')#调用方归一化查询：操作、源路径、光标、工作区根
语言服务器提供方查询字段=('operation','filePath','position','workspaceRoot','languageId')#提供方收到的查询：调用方请求加推导出的语言 id
语言服务器定位字段=('uri','range')#一处已解析位置：文档 URI 及其内部范围
语言服务器悬停字段=('contents','range')#归一化悬停：正文与可选范围
语言服务器查询结果种类=('locations','hover')#封闭结果联合的 kind：导航为 locations，悬停为 hover
语言服务器提供方字段=('id','extensionToLanguage','query')#语言服务器后端：品牌 id、扩展映射、查询入口
语言服务器服务字段=('registerProvider','query')#LSP 能力缝：注册提供方与按扩展路由查询（上游方法名字面量）
