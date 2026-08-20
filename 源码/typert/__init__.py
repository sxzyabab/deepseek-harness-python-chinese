"""Typert 包聚合：协议 + 注册表 + loader。

公开面仅中文名。
"""
from typert.protocol import (#协议
    是否合法远程段,查找策略失败,Typert查找失败,
    绑定远程网关,远程服务,远程,远程作用域,远程方法们,
)#协议
from typert.registry import (#注册表
    拼模式键,拼包面键,拼端点,Typert注册表,应用 as 应用注册表,
)#注册表
from typert import loader as 加载器#Loader 集成

__all__=[#公开面
    '是否合法远程段','查找策略失败','Typert查找失败',
    '绑定远程网关','远程服务','远程','远程作用域','远程方法们',
    '拼模式键','拼包面键','拼端点','Typert注册表','应用注册表',
    '加载器',
]#结束
