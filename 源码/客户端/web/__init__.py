from .启动 import 网页应用入口#Web 入口
from .种子 import 静态模块表#静态模块表
from .应用注入 import 应用索引注入#索引注入

__all__=['应用','网页应用入口','静态模块表','应用索引注入']#仅中文公开名

def 应用():
    """Vite 入口与模块表在浏览器半边；宿主无行为。"""
    return#空 apply

apply=应用#框架槽
