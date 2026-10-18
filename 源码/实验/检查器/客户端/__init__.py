'浏览器 Client 入口。导出同目录模块，不由宿主调用'
from .插件 import 应用,名称,依赖
from . import 插件,cdp,桥接,检视,底栏

__all__=['应用','名称','依赖','插件','cdp','桥接','检视','底栏']

name=名称
inject=依赖
apply=应用
