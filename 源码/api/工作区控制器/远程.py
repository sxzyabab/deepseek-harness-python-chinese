"""工作区控制器的 Host-for-Client Remote 贡献。

注册 workspace 命名空间 create/rename/delete/insertBefore/
insertSessionBefore/archiveSession/follow；directoryPicker 命名空间 pick/list/createDirectory。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['默认','远程贡献表']#仅中文公开名；TYPERT_REMOTE 为 typert 框架槽不入表

包名='@deepseek-ai/dsh-api-workspace-controller'工作区服务='workspaceController'#服务键
工作区命名空间='workspace'#命名空间
目录服务='directoryPickerController'#目录服务键
目录命名空间='directoryPicker'#目录命名空间
工作区前=包名+'#WorkspaceController.'#工作区 id 前缀
目录前=包名+'#DirectoryPickerController.'#目录 id 前缀
流式={'kind':'direct','mode':'stream'}#流式调用

远程贡献表=远程贡献(包名,[#贡献
    调用描述符(工作区前+'create',工作区服务,工作区命名空间,'create',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('WorkspaceCreateRequest')}],
        严格编解码('WorkspaceCreateValue'),{'file':'src/index.ts','line':57,'column':3}),
    调用描述符(工作区前+'rename',工作区服务,工作区命名空间,'rename',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('WorkspaceRenameRequest')}],
        严格编解码('WorkspaceValue'),{'file':'src/index.ts','line':67,'column':3}),
    调用描述符(工作区前+'delete',工作区服务,工作区命名空间,'delete',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('WorkspaceDeleteRequest')}],
        严格编解码('WorkspaceDeleteValue'),{'file':'src/index.ts','line':77,'column':3}),
    调用描述符(工作区前+'insertBefore',工作区服务,工作区命名空间,'insertBefore',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('WorkspaceInsertBeforeRequest')}],
        严格编解码('WorkspaceOrderValue'),{'file':'src/index.ts','line':87,'column':3}),
    调用描述符(工作区前+'insertSessionBefore',工作区服务,工作区命名空间,'insertSessionBefore',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('WorkspaceInsertSessionBeforeRequest')}],
        严格编解码('WorkspaceValue'),{'file':'src/index.ts','line':97,'column':3}),
    调用描述符(工作区前+'archiveSession',工作区服务,工作区命名空间,'archiveSession',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('WorkspaceArchiveSessionRequest')}],
        严格编解码('WorkspaceArchiveValue'),{'file':'src/index.ts','line':107,'column':3}),
    调用描述符(工作区前+'follow',工作区服务,工作区命名空间,'follow',
        [],严格编解码('WorkspaceFollowFrame'),{'file':'src/index.ts','line':117,'column':3},
        调用=流式,取消={'parameter':'signal'}),
    调用描述符(目录前+'pick',目录服务,目录命名空间,'pick',
        [],严格编解码('string | null'),{'file':'src/directory-picker.ts','line':54,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(目录前+'list',目录服务,目录命名空间,'list',
        [{'name':'path','wire':'path','source':'json','codec':严格编解码('string | undefined')}],
        严格编解码('DirectoryListing'),{'file':'src/directory-picker.ts','line':71,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(目录前+'createDirectory',目录服务,目录命名空间,'createDirectory',
        [
            {'name':'path','wire':'path','source':'json','codec':严格编解码('string')},
            {'name':'name','wire':'name','source':'json','codec':严格编解码('string')},
        ],
        严格编解码('string'),{'file':'src/directory-picker.ts','line':87,'column':3}),
])#结束
默认=远程贡献表
TYPERT_REMOTE=远程贡献表#typert框架槽
