"""向 typert 注册会话引用的远程候选查询贡献。"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['默认','远程贡献表']#仅中文公开名；TYPERT_REMOTE 为 typert 框架槽不入表

包名='@deepseek-ai/dsh-session-reference'服务='sessionReferenceResolver'#服务键
命名空间='sessionReferenceResolver'#命名空间
类前=包名+'#SessionReferenceResolver.'#调用 id 前缀
智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}#结束
作用域={'context':'agent','wire':'agent'}#agent scope

远程贡献表=远程贡献(包名,[#贡献
    调用描述符(类前+'remoteExportCandidates',服务,命名空间,'candidates',
        [智能体参数,{'name':'query','wire':'query','source':'json','codec':严格编解码('string')}],
        严格编解码('SessionReferenceMentionCandidate[]'),{'file':'src/index.ts','line':273,'column':3},
        实现='remoteExportCandidates',作用域=作用域,取消={'parameter':'signal'}),
])#结束
默认=远程贡献表
TYPERT_REMOTE=远程贡献表#typert框架槽
