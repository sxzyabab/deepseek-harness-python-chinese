"""文件上传 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：upload。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-client-file-upload'#上游包名
服务='fileUploads'#服务键
命名空间='fileUploads'#命名空间
类前=包名+'#FileUploadService.'#调用 id 前缀
智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}#结束
作用域={'context':'agent','wire':'agent'}#agent scope

TYPERT_REMOTE=远程贡献(包名,[#贡献
    调用描述符(类前+'upload',服务,命名空间,'upload',
        [智能体参数,{'name':'request','wire':'request','source':'json','codec':严格编解码('EncodedFileUploadRequest')}],
        严格编解码('FileUploadValue'),{'file':'src/index.ts','line':105,'column':3},
        实现='上传',作用域=作用域,取消={'parameter':'signal'}),
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
