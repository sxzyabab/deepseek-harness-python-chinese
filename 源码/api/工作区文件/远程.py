"""工作区文件 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：read / readBytes / readAll / readRelated / stat / list / changes。
首参为 workspaceFileScope 查找。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-api-workspace-files'#上游包名
服务='workspaceFiles'#服务键
命名空间='workspaceFiles'#命名空间
类前=包名+'#WorkspaceFiles.'#调用 id 前缀
作用域参数={#workspaceFileScope lookup
    'name':'workspaceFileScope','wire':'workspaceFileScopeId','source':'lookup','lookup':'workspaceFileScope',
    'codec':严格编解码('WorkspaceFileScope'),
}#结束
流式={'kind':'direct','mode':'stream'}#流式

TYPERT_REMOTE=远程贡献(包名,[#贡献
    调用描述符(类前+'read',服务,命名空间,'read',
        [作用域参数,
         {'name':'path','wire':'path','source':'json','codec':严格编解码('string')},
         {'name':'range','wire':'range','source':'json','codec':严格编解码('WorkspaceFileRange')}],
        严格编解码('WorkspaceFileText'),{'file':'src/index.ts','line':232,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(类前+'readBytes',服务,命名空间,'readBytes',
        [作用域参数,
         {'name':'path','wire':'path','source':'json','codec':严格编解码('string')},
         {'name':'range','wire':'range','source':'json','codec':严格编解码('WorkspaceByteRange')}],
        严格编解码('WorkspaceFileBytes'),{'file':'src/index.ts','line':257,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(类前+'readAll',服务,命名空间,'readAll',
        [作用域参数,{'name':'path','wire':'path','source':'json','codec':严格编解码('string')}],
        严格编解码('WorkspaceFileBytes'),{'file':'src/index.ts','line':278,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(类前+'readRelated',服务,命名空间,'readRelated',
        [作用域参数,
         {'name':'path','wire':'path','source':'json','codec':严格编解码('string')},
         {'name':'relativePath','wire':'relativePath','source':'json','codec':严格编解码('string')}],
        严格编解码('WorkspaceFileBytes'),{'file':'src/index.ts','line':300,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(类前+'stat',服务,命名空间,'stat',
        [作用域参数,{'name':'path','wire':'path','source':'json','codec':严格编解码('string')}],
        严格编解码('WorkspaceFileStat'),{'file':'src/index.ts','line':324,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(类前+'list',服务,命名空间,'list',
        [作用域参数,{'name':'path','wire':'path','source':'json','codec':严格编解码('string')}],
        严格编解码('WorkspaceDirectoryListing'),{'file':'src/index.ts','line':337,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(类前+'changes',服务,命名空间,'changes',
        [作用域参数],严格编解码('WorkspaceFileWatchFrame'),{'file':'src/index.ts','line':365,'column':3},
        调用=流式,取消={'parameter':'signal'}),
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
