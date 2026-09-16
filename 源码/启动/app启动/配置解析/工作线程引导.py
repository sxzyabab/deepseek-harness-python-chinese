"""在一个 Harness 拥有的工作线程里安装继承的配置解析世代。"""
from .解析器 import 安装配置解析,取工作线程登记#解析器登记

登记=取工作线程登记()#线程环境数据
if 登记 is not None:#有继承世代
    安装配置解析(登记['generation'],登记['behavior'])#安装
