'发现页的宿主入口。pluginMarket 服务由它自己的组合包提供'
from . import 客户端

__all__=['客户端','名称','应用']

名称='ui-plugin-market'

def 应用():
    '宿主入口不增加行为'
    return None

name=名称
apply=应用
default=应用
