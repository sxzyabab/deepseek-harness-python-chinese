from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['默认','远程贡献表']#仅中文公开名

包名='@deepseek-ai/dsh-client-file-upload'
服务='fileUploads'#服务键
命名空间='fileUploads'#命名空间
类前=包名+'#FileUploadService.'#调用 id 前缀
智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}
作用域={'context':'agent','wire':'agent'}#agent scope

远程贡献表=远程贡献(包名,[#贡献
    调用描述符(类前+'upload',服务,命名空间,'upload',
        [智能体参数,{'name':'request','wire':'request','source':'json','codec':严格编解码('EncodedFileUploadRequest')}],
        严格编解码('FileUploadValue'),{'file':'src/index.ts','line':105,'column':3},
        实现='上传',作用域=作用域,取消={'parameter':'signal'}),
])
默认=远程贡献表

