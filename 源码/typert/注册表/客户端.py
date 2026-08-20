"""共享 Typert 运行时注册表的客户端面。

对齐上游 `typert/registry/src/client/index.ts`。公开面仅中文名。
"""
from ..服务 import Typert注册表#与宿主面相同的注册表实现

注入=[]#不注入其他服务；本插件是客户端反射根
inject=注入#上游名

def 应用(上下文):#在客户端根上安装注册表
    """安装与宿主面相同的注册表实现。"""
    Typert注册表(上下文)#构造并挂上

apply=应用#上游名

__all__=['注入','inject','应用','apply']#公开面
