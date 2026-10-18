from ...依赖.schemastery import 字符串字段
from .语言设置 import (
    语言设置命名空间,
    语言偏好字段,
    语言标识模式,
    语言标识表,
)
from . import (
    客户端,
    词表,
    异常,
    语言设置,
)

__all__=[
    '应用','配置',
    '语言设置命名空间','语言偏好字段','语言标识表',
    '客户端','词表','异常','语言设置',
]

易失偏好=字符串字段(格式=语言标识模式,可空=True)#运行中可更新的偏好
易失偏好.meta={'volatile':True}
配置={语言偏好字段:易失偏好}#投影到浏览器的宿主偏好
Config=配置

def 应用(上下文):
    '宿主偏好经配置表单投影。这里只关掉设置面的自动呈现，不调用客户端'
    def 接线(子上下文):
        '有 settings 才关掉自动呈现'
        def 挂():
            'auto 为 false，绑到本纤程'
            return 子上下文.settings.configure({'auto':False},上下文.纤程)
        return 子上下文.副作用(挂)
    上下文.依赖启动(['settings'],接线)

apply=应用
