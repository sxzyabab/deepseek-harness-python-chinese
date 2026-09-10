"""插件清单 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：list。公开面仅中文名。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-host-plugin-inventory'#上游包名
服务='pluginInventory'#服务键
命名空间='pluginInventory'#命名空间
类前=包名+'#PluginInventory.'#调用 id 前缀

TYPERT_REMOTE=远程贡献(包名,[#贡献
    调用描述符(类前+'list',服务,命名空间,'list',
        [],严格编解码('PluginInventorySnapshot'),{'file':'src/index.ts','line':65,'column':3}),
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
