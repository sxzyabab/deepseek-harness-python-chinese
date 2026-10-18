from ....模块.客户端.通告 import 取握手窗口
import os
from ....ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['样式模块','确保浏览器样式','标浏览器']

样式模块='sidebar-browser'
样式路径=os.path.join(os.path.dirname(__file__),'浏览器.module.css')


def 取窗口(属性=None):
    '调用方带来的窗口，否则用桥上的窗口'
    if isinstance(属性,dict) and 属性.get('window') is not None:
        return 属性['window']
    return 取握手窗口()


def 确保浏览器样式(文档):
    '浏览器模块样式按文档只插一次'
    注入模块样式文件(文档,'侧边栏浏览器样式',样式路径,样式模块)


def 标浏览器(节点,类名=None):
    '挂上游类名，再用模块属性接上编译后的选择器'
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    标样式模块(节点,样式模块)
    return 节点
