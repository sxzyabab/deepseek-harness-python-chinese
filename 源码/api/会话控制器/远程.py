"""会话控制器的 Host-for-Client Remote 贡献。

注册 session / skills / fileReferences 命名空间方法。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['默认','远程贡献表']#仅中文公开名；TYPERT_REMOTE 为 typert 框架槽不入表

包名='@deepseek-ai/dsh-api-session-controller'会话服务='sessionController'#会话服务键
会话命名空间='session'#会话命名空间
技能服务='sessionSkillCatalog'#技能服务键
技能命名空间='skills'#技能命名空间
文件引用服务='sessionFileReferences'#文件引用服务键
文件引用命名空间='fileReferences'#文件引用命名空间
会话前=包名+'#SessionController.'#会话前缀
技能前=包名+'#SessionSkillCatalog.'#技能前缀
文件前=包名+'#SessionFileReferences.'#文件前缀
智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}
作用域={'context':'agent','wire':'agent'}#agent scope
流式={'kind':'direct','mode':'stream'}#流式

远程贡献表=远程贡献(包名,[#贡献
    调用描述符(会话前+'list',会话服务,会话命名空间,'list',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionListRequest')}],
        严格编解码('SessionListValue'),{'file':'src/index.ts','line':217,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(会话前+'search',会话服务,会话命名空间,'search',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionSearchRequest')}],
        严格编解码('SessionSearchValue'),{'file':'src/index.ts','line':228,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(会话前+'create',会话服务,会话命名空间,'create',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionCreateRequest')}],
        严格编解码('SessionCreateValue'),{'file':'src/index.ts','line':238,'column':3}),
    调用描述符(会话前+'selectModel',会话服务,会话命名空间,'selectModel',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionSelectModelRequest')}],
        严格编解码('SessionSelectModelValue'),{'file':'src/index.ts','line':248,'column':3}),
    调用描述符(会话前+'modelCatalog',会话服务,会话命名空间,'modelCatalog',
        [],严格编解码('SessionModelCatalog'),{'file':'src/index.ts','line':257,'column':3}),
    调用描述符(会话前+'canOpenWorkspacePath',会话服务,会话命名空间,'canOpenWorkspacePath',
        [],严格编解码('boolean'),{'file':'src/index.ts','line':266,'column':3}),
    调用描述符(会话前+'openWorkspacePath',会话服务,会话命名空间,'openWorkspacePath',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionOpenWorkspacePathRequest')}],
        严格编解码('SessionOpenWorkspacePathValue'),{'file':'src/index.ts','line':278,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(会话前+'rename',会话服务,会话命名空间,'rename',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionRenameRequest')}],
        严格编解码('SessionRenameValue'),{'file':'src/index.ts','line':309,'column':3}),
    调用描述符(会话前+'fork',会话服务,会话命名空间,'fork',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionForkRequest')}],
        严格编解码('SessionForkValue'),{'file':'src/index.ts','line':319,'column':3}),
    调用描述符(会话前+'prompt',会话服务,会话命名空间,'prompt',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionPromptRequest')}],
        严格编解码('SessionPromptValue'),{'file':'src/index.ts','line':330,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(会话前+'attachment',会话服务,会话命名空间,'attachment',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionAttachmentRequest')}],
        严格编解码('SessionAttachmentValue'),{'file':'src/index.ts','line':341,'column':3}),
    调用描述符(会话前+'updateQueue',会话服务,会话命名空间,'updateQueue',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionUpdateQueueRequest')}],
        严格编解码('SessionUpdateQueueValue'),{'file':'src/index.ts','line':351,'column':3}),
    调用描述符(会话前+'cancel',会话服务,会话命名空间,'cancel',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionCancelRequest')}],
        严格编解码('SessionCancelValue'),{'file':'src/index.ts','line':361,'column':3}),
    调用描述符(会话前+'page',会话服务,会话命名空间,'page',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionPageRequest')}],
        严格编解码('SessionPageValue'),{'file':'src/index.ts','line':372,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(会话前+'follow',会话服务,会话命名空间,'follow',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SessionFollowRequest')}],
        严格编解码('SessionFollowFrame'),{'file':'src/index.ts','line':384,'column':3},
        调用=流式,取消={'parameter':'signal'}),
    调用描述符(会话前+'control',会话服务,会话命名空间,'control',
        [],严格编解码('SessionControlFrame'),{'file':'src/index.ts','line':394,'column':3},
        调用=流式,取消={'parameter':'signal'}),
    调用描述符(技能前+'list',技能服务,技能命名空间,'list',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SkillListRequest')}],
        严格编解码('SkillListValue'),{'file':'src/skill-catalog.ts','line':35,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(文件前+'list',文件引用服务,文件引用命名空间,'list',
        [智能体参数,{'name':'query','wire':'query','source':'json','codec':严格编解码('string')}],
        严格编解码('FileReferenceCandidate[]'),{'file':'src/file-references.ts','line':32,'column':3},
        作用域=作用域,取消={'parameter':'signal'}),
])
默认=远程贡献表
TYPERT_REMOTE=远程贡献表#typert框架槽
