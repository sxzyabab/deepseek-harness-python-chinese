"""已授权 Office 输入与完整 PDF 输出的线协议与包内约定。

跨包结果为 dict。错误码、优先级、扩展名与 Remote 详情键保持英文。
"""
from .标识构造 import office源键,office转pdf世代,office转pdf键#再导出身份

__all__=[#仅中文公开名
    'office源键','office转pdf世代','office转pdf键',
    'office扩展名表','office转pdf优先级表','office转pdf错误码表',
    '已渲染文档字节字段',
]#公开面结束

#常量
office扩展名表=('doc','docx','xls','xlsx','ppt','pptx')#支持的二进制与 OOXML 扩展名
office转pdf优先级表=('foreground','background')#前台预览优先于后台推测
office转pdf错误码表=(#消费者可展示的分类码
    'input-too-large','output-too-large','invalid-document','unsupported-format',
    'invalid-output','timeout','unavailable','failed','busy','source-changed',
)#错误码结束
已渲染文档字节字段=(#RenderedDocumentBytes：工作区文件字节 + 缺失字体与世代
    'absolutePath','version','offset','eof','bytes','data','missingFonts','generation',
)#字段结束
