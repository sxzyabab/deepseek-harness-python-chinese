"""声明插件清单远程 list 贡献。"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献

__all__=['默认','远程贡献表']

包名='@deepseek-ai/dsh-host-plugin-inventory'
服务='pluginInventory'#远程服务键
命名空间='pluginInventory'
类前=包名+'#PluginInventory.'#调用 id 前缀

远程贡献表=远程贡献(包名,[
    调用描述符(类前+'list',服务,命名空间,'list',
        [],严格编解码('PluginInventorySnapshot'),{'file':'src/index.ts','line':65,'column':3}),
])
默认=远程贡献表
default=远程贡献表#框架槽
