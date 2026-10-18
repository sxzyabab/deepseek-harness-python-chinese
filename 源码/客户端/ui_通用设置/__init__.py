from ...依赖.schemastery import 字符串字段
from . import (
    客户端,
    异常,
    类型,
)

__all__=['应用','配置','客户端','异常','类型']

欢迎通知版本=字符串字段(可空=True)
欢迎通知版本.meta={'volatile':True}
配置={'welcomeNoticeVersion':欢迎通知版本}
Config=配置

def 应用(上下文):
    '有 settings 时关掉本插件的自动设置页。不调用客户端应用'
    def 接线(子上下文):
        '把 auto 设为 false，绑到本纤程'
        def 挂():
            '登记呈现策略，拆除器由 configure 交回'
            return 子上下文.settings.configure({'auto':False},上下文.纤程)
        return 子上下文.副作用(挂)
    上下文.依赖启动(['settings'],接线)

apply=应用
