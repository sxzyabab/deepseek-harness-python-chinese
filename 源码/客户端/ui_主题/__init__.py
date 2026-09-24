from .启动主题 import 注入启动主题,启动主题注入行#主题启动脚本注入
from .主题设置 import (
    默认偏好,
    默认字号,
    主题偏好字段,
    主题偏好表,
    主题设置命名空间,
    主题设置模式,
    字号字段,
    字号最小,
    字号最大,
    是否主题偏好,
)

__all__=[
    '应用','配置',
    '默认偏好','默认字号','主题偏好字段','主题偏好表','主题设置命名空间',
    '主题设置模式','字号字段','字号最小','字号最大','是否主题偏好',
]

配置={
    'preference':默认偏好,
    'fontSize':默认字号,
}

def 读易失(字段):
    """插件配置易失字段；有 get 则调，否则当值。"""
    if hasattr(字段,'get') and callable(字段.get):
        return 字段.get()
    return 字段

def 应用(上下文,配置对象=None):
    """关掉设置自动呈现，并把当前易失偏好注入 index。"""
    def 接线(子上下文):
        """有 settings 才关掉自动呈现。"""
        def 挂():
            """auto:false 绑到本纤程。"""
            return 子上下文.settings.configure({'auto':False},上下文.纤程)
        子上下文.副作用(挂)
    上下文.依赖启动(['settings'],接线)
    def 注入索引(表):
        """把启动主题行推入注入表。"""
        源=配置 if 配置对象 is None else 配置对象
        偏好=读易失(源['preference'])
        字号=读易失(源['fontSize'])
        表.extend(启动主题注入行(偏好,字号))
    上下文.监听('webserver/index-inject',注入索引)

apply=应用
Config=配置
