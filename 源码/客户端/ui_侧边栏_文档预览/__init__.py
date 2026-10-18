from . import 客户端,异常
from .配置 import 配置

__all__=['应用','客户端','异常','配置']

def 应用(上下文,配置对象):
    '把已校验的预览上限注入浏览器页面。拆插件时监听一并卸下'
    def 注入(表):
        '写入全局配置名'
        表.append({'kind':'global','name':'__DSH_DOCUMENT_PREVIEW_CONFIG__','value':配置对象})
    上下文.监听('webserver/index-inject',注入)

apply=应用
Config=配置
