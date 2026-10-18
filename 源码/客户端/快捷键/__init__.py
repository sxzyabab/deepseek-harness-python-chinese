'窗口级键盘序列的宿主配置注入'
from . import (
    异常,
    原生,
    持久化,
    绑定,
    配置文档,
    协议,
    客户端,
)
from .配置 import 配置#时序校验

__all__=[#同目录模块。配置是宿主导出的校验函数，不转发客户端里的类
    '应用','配置','apply','Config',
    '异常','原生','持久化','绑定','配置文档','协议','客户端',
]

def 应用(上下文,配置值):
    '把已校验的键盘时序写入页面初始化表'
    def 注入(表):
        '追加一条全局注入'
        表.append({'kind':'global','name':'__DSH_SHORTCUTS_CONFIG__','value':配置值})#注入
    上下文.监听('webserver/index-inject',注入)#登记

apply=应用#框架槽
Config=配置#框架槽
