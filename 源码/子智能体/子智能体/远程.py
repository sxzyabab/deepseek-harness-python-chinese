"""子智能体 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：list / prompt / interruptByParent。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-subagent'#上游包名
服务='subagents'#服务键
命名空间='subagents'#命名空间
类前=包名+'#SubagentRuntime.'#调用 id 前缀

TYPERT_REMOTE=远程贡献(包名,[#贡献
    调用描述符(类前+'remoteExportList',服务,命名空间,'list',
        [{'name':'parentSessionId','wire':'parentSessionId','source':'json','codec':严格编解码('SessionId')}],
        严格编解码('SubagentCatalog'),{'file':'src/index.ts','line':382,'column':3},
        实现='remoteExportList',取消={'parameter':'signal'}),
    调用描述符(类前+'prompt',服务,命名空间,'prompt',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SubagentPromptRequest')}],
        严格编解码('SubagentPromptReceipt'),{'file':'src/index.ts','line':409,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(类前+'interruptByParent',服务,命名空间,'interruptByParent',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('SubagentInterruptRequest')}],
        严格编解码('SubagentInterruptReceipt'),{'file':'src/index.ts','line':476,'column':3}),
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
