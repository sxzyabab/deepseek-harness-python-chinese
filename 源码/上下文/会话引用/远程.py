"""会话引用 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：candidates。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-session-reference'#上游包名
服务='sessionReferenceResolver'#服务键
命名空间='sessionReferenceResolver'#命名空间
类前=包名+'#SessionReferenceResolver.'#调用 id 前缀
智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}#结束
作用域={'context':'agent','wire':'agent'}#agent scope

TYPERT_REMOTE=远程贡献(包名,[#贡献
    调用描述符(类前+'remoteExportCandidates',服务,命名空间,'candidates',
        [智能体参数,{'name':'query','wire':'query','source':'json','codec':严格编解码('string')}],
        严格编解码('SessionReferenceMentionCandidate[]'),{'file':'src/index.ts','line':273,'column':3},
        实现='remoteExportCandidates',作用域=作用域,取消={'parameter':'signal'}),
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
