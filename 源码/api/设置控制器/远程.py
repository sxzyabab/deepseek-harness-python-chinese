"""设置控制器 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：settings 命名空间 describe/canOpenAgentPresetDirectory/update/replace/
mutate/openSettingsDocument/openAgentPresetDirectory；credentials 命名空间 describe/set/unset。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-api-settings-controller'#上游包名
设置服务='settingsController'#设置服务键
设置命名空间='settings'#设置命名空间
凭据服务='credentialsController'#凭据服务键
凭据命名空间='credentials'#凭据命名空间
设置前=包名+'#SettingsController.'#设置前缀
凭据前=包名+'#CredentialsController.'#凭据前缀

TYPERT_REMOTE=远程贡献(包名,[#贡献
    调用描述符(设置前+'describe',设置服务,设置命名空间,'describe',
        [],严格编解码('SettingsDescribeValue'),{'file':'src/index.ts','line':116,'column':3}),
    调用描述符(设置前+'canOpenAgentPresetDirectory',设置服务,设置命名空间,'canOpenAgentPresetDirectory',
        [],严格编解码('boolean'),{'file':'src/index.ts','line':130,'column':3}),
    调用描述符(设置前+'update',设置服务,设置命名空间,'update',
        [
            {'name':'ns','wire':'ns','source':'json','codec':严格编解码('string')},
            {'name':'patch','wire':'patch','source':'json','codec':严格编解码('Record<string, JsonValue>')},
            {'name':'expectedRevision','wire':'expectedRevision','source':'json','codec':严格编解码('number | undefined')},
        ],
        严格编解码('SettingsNamespaceView'),{'file':'src/index.ts','line':143,'column':3}),
    调用描述符(设置前+'replace',设置服务,设置命名空间,'replace',
        [
            {'name':'ns','wire':'ns','source':'json','codec':严格编解码('string')},
            {'name':'section','wire':'section','source':'json','codec':严格编解码('Record<string, JsonValue>')},
            {'name':'expectedRevision','wire':'expectedRevision','source':'json','codec':严格编解码('number | undefined')},
        ],
        严格编解码('SettingsNamespaceView'),{'file':'src/index.ts','line':160,'column':3}),
    调用描述符(设置前+'mutate',设置服务,设置命名空间,'mutate',
        [
            {'name':'ns','wire':'ns','source':'json','codec':严格编解码('string')},
            {'name':'ops','wire':'ops','source':'json','codec':严格编解码('SettingsPathOpView[]')},
            {'name':'expectedRevision','wire':'expectedRevision','source':'json','codec':严格编解码('number | undefined')},
        ],
        严格编解码('SettingsNamespaceView'),{'file':'src/index.ts','line':179,'column':3}),
    调用描述符(设置前+'openSettingsDocument',设置服务,设置命名空间,'openSettingsDocument',
        [],严格编解码('SettingsDocumentOpenValue'),{'file':'src/index.ts','line':194,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(设置前+'openAgentPresetDirectory',设置服务,设置命名空间,'openAgentPresetDirectory',
        [{'name':'agentPreset','wire':'agentPreset','source':'json','codec':严格编解码('string')}],
        严格编解码('AgentPresetDirectoryOpenValue'),{'file':'src/index.ts','line':225,'column':3},
        取消={'parameter':'signal'}),
    调用描述符(凭据前+'describe',凭据服务,凭据命名空间,'describe',
        [{'name':'refs','wire':'refs','source':'json','codec':严格编解码('string[]')}],
        严格编解码('Record<string, CredentialInfo>'),{'file':'src/credentials.ts','line':82,'column':3}),
    调用描述符(凭据前+'set',凭据服务,凭据命名空间,'set',
        [
            {'name':'ref','wire':'ref','source':'json','codec':严格编解码('string')},
            {'name':'value','wire':'value','source':'json','codec':严格编解码('string')},
        ],
        严格编解码('void'),{'file':'src/credentials.ts','line':99,'column':3}),
    调用描述符(凭据前+'unset',凭据服务,凭据命名空间,'unset',
        [{'name':'ref','wire':'ref','source':'json','codec':严格编解码('string')}],
        严格编解码('void'),{'file':'src/credentials.ts','line':112,'column':3}),
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
