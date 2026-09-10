"""智能体预设 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：list / read / copy / deletePreset / select。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-agent-presets'#上游包名
服务='agentPresets'#服务键
命名空间='agentPresets'#命名空间
类前=包名+'#AgentPresets.'#调用 id 前缀

TYPERT_REMOTE=远程贡献(包名,[#贡献
    调用描述符(类前+'remoteExportList',服务,命名空间,'list',
        [],严格编解码('AgentPresetRoster'),{'file':'src/index.ts','line':260,'column':3},
        实现='remoteExportList'),
    调用描述符(类前+'read',服务,命名空间,'read',
        [{'name':'id','wire':'id','source':'json','codec':严格编解码('string')}],
        严格编解码('AgentPresetReadValue'),{'file':'src/index.ts','line':512,'column':3}),
    调用描述符(类前+'copy',服务,命名空间,'copy',
        [{'name':'request','wire':'request','source':'json','codec':严格编解码('AgentPresetCopyRequest')}],
        严格编解码('AgentPresetCopyValue'),{'file':'src/index.ts','line':564,'column':3}),
    调用描述符(类前+'deletePreset',服务,命名空间,'deletePreset',
        [{'name':'id','wire':'id','source':'json','codec':严格编解码('string')}],
        严格编解码('AgentPresetDeleteValue'),{'file':'src/index.ts','line':602,'column':3}),
    调用描述符(类前+'select',服务,命名空间,'select',
        [{'name':'id','wire':'id','source':'json','codec':严格编解码('string')}],
        严格编解码('AgentPresetSelectValue'),{'file':'src/index.ts','line':694,'column':3}),
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
