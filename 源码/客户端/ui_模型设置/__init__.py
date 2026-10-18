from . import (
    上手引导配置,
    客户端,
    引导文案,
    异常,
)
from .上手引导配置 import 上手引导配置全局键,配置

__all__=['应用','配置','客户端','异常','上手引导配置','引导文案']

def 应用(上下文,配置值):
    '在浏览器插件激活前，把凭据引导选项写进页面'
    def 注入(表):
        '写入页面全局'
        表.append({
            'kind':'global',
            'name':上手引导配置全局键,
            'value':{'credentialOnboarding':配置值['credentialOnboarding']},
        })
    上下文.监听('webserver/index-inject',注入)

apply=应用
Config=配置
