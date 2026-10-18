from ...依赖.schemastery import 布尔字段
from .开发者工具设置 import 开发者工具设置字段
from . import (
    客户端,
    异常,
    开发者工具设置,
)

__all__=['应用','配置','客户端','异常','开发者工具设置']

运行期启用=布尔字段(默认值=True)#易失副本，不改持久字段
运行期启用.meta={'volatile':True}#运行中可更新
配置={'enabled':运行期启用}#投影到浏览器的宿主偏好
Config=配置

def 应用(上下文):
    '宿主偏好经配置表单投影。这里只关掉设置面的自动呈现'
    def 接线(子上下文):
        '有 settings 才关掉自动呈现'
        def 挂():
            'auto 为 false，绑到本纤程'
            return 子上下文.settings.configure({'auto':False},上下文.纤程)
        子上下文.副作用(挂)
    上下文.依赖启动(['settings'],接线)

apply=应用
