"""LSP 能力缝词汇与品牌类型。"""
语言服务器操作=('goToDefinition','findReferences','goToImplementation','hover')#四种语义查询
语言服务器位置字段=('line','character')#零基 UTF-16 光标
语言服务器范围字段=('start','end')#半开区间
语言服务器查询请求字段=('operation','filePath','position','workspaceRoot')#归一化查询
语言服务器提供方查询字段=语言服务器查询请求字段+('languageId',)#提供方收到的查询
语言服务器位置记录字段=('uri','range')#单条位置
语言服务器悬停字段=('contents','range')#悬停正文与可选范围

__all__=[#仅中文公开名
    '语言服务器操作','语言服务器位置字段','语言服务器范围字段',
    '语言服务器查询请求字段','语言服务器提供方查询字段',
    '语言服务器位置记录字段','语言服务器悬停字段',
]#公开面结束
