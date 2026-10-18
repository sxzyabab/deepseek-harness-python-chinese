'浏览器面的共享 Typert 运行时注册表'
from ..服务 import Typert注册表#与宿主面相同的注册表实现

依赖=[]#不注入其他服务。本插件是客户端反射根
inject=依赖#框架槽

def 应用(上下文,配置=None):
    '安装与宿主面相同的注册表实现'
    Typert注册表(上下文,配置)#构造并挂上 typert 服务

apply=应用#框架槽
__all__=[#公开名
    '依赖','inject','应用','apply',
]#公开面
