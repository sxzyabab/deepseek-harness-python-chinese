from . import 客户端 as 客户端包
from .联系配置 import 配置,联系配置全局键,解析联系配置

__all__=['应用','配置','联系配置全局键']

def 应用(上下文,配置值=None):
    """在浏览器插件启动前把公开问卷选项写入页面初始化表。"""
    已解析=解析联系配置(配置值)
    def 注入(表):
        """追加一条全局注入。"""
        表.append({'kind':'global','name':联系配置全局键,'value':已解析})
    上下文.监听('webserver/index-inject',注入)

apply=应用
Config=配置
