from .提供方 import 宿主巡检提供方

__all__=['名称','依赖','应用','默认']

名称='cordis-inspect-providers'
依赖=['cordisInspect','tools']

def 应用(上下文):
    """按进程登记第一方宿主巡检提供方。注册表按 id 去重，本行挂在宿主组合里。"""
    for 提供方 in 宿主巡检提供方(上下文):
        def 登记效果(当前=提供方):
            """把该提供方挂进巡检注册表。"""
            return 上下文.cordisInspect.登记(当前)
        上下文.副作用(登记效果,'cordis-inspect-providers: '+提供方.清单['id'])

name=名称
inject=依赖
apply=应用
default=应用
默认=应用
