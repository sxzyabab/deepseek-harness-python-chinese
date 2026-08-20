"""插件清单 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote('list')`：无参快照。服务键与命名空间均为 `pluginInventory`。
"""
from typert.protocol import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

包名='@deepseek-ai/dsh-host-plugin-inventory'#上游包名
服务='pluginInventory'#服务键
命名空间='pluginInventory'#命名空间

清单描述符=调用描述符(#pluginInventory/list
    包名+'#PluginInventoryGateway.list',#id
    服务,命名空间,'list',#service/ns/method
    [],#无参
    严格编解码('PluginInventorySnapshot'),#result
    {'file':'src/index.ts','line':56,'column':3},#sourceLocation
)#结束

TYPERT_REMOTE=远程贡献(包名,[清单描述符])#贡献
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
