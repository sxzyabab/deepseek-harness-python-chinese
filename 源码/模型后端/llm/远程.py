"""LLM Host-for-Client Remote 贡献。

对照 `@Remote`：listProviders / listConfigurableProviders / discoverModels。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['默认','远程贡献表']#仅中文公开名；TYPERT_REMOTE 为 typert 框架槽不入表

包名='@deepseek-ai/dsh-llm'#插件包名
服务='llm'#服务键
命名空间='llm'#命名空间
类前=包名+'#LlmRuntime.'#调用 id 前缀

远程贡献表=远程贡献(包名,[#贡献
    调用描述符(类前+'listProviders',服务,命名空间,'listProviders',
        [],严格编解码('LlmProviderInfo[]'),{'file':'src/index.ts','line':468,'column':3}),
    调用描述符(类前+'listConfigurableProviders',服务,命名空间,'listConfigurableProviders',
        [],严格编解码('LlmConfigurableProvider[]'),{'file':'src/index.ts','line':540,'column':3}),
    调用描述符(类前+'remoteDiscoverModels',服务,命名空间,'discoverModels',
        [
            {'name':'settingsNs','wire':'settingsNs','source':'json','codec':严格编解码('string')},
            {'name':'request','wire':'request','source':'json','codec':严格编解码('LlmModelDiscoveryRequest')},
        ],
        严格编解码('LlmDiscoveredModel[]'),{'file':'src/index.ts','line':627,'column':3},
        实现='remoteDiscoverModels',取消={'parameter':'signal'}),
])#结束
默认=远程贡献表
TYPERT_REMOTE=远程贡献表#typert框架槽
