"""共享 Typert 运行时注册表的宿主入口。

对齐上游 `typert/registry/src/index.ts`。公开面仅中文名。
"""
from .服务 import (#注册表实现与键构造
    拼模式键,拼包面键,拼端点,Typert注册表,
    typertKey,typertPackageKey,typertEndpoint,TypertRegistry,
)#服务
from .类型 import *#类型锚点

名称='typert'#插件名（字面量）
注入=[]#无硬依赖；本插件是反射根

def 应用(上下文):#在宿主根上安装注册表
    """安装与客户端面相同的注册表实现。"""
    Typert注册表(上下文)#构造并挂上

apply=应用#上游名

__all__=[#公开面
    '拼模式键','拼包面键','拼端点','Typert注册表',
    'typertKey','typertPackageKey','typertEndpoint','TypertRegistry',
    '名称','注入','应用','apply',
]#结束
