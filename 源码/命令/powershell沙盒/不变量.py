"""本包拥有的不变量配套（中文名包）。"""
from importlib import import_module as 导入模块#带连字符目录需经 importlib
源模块=导入模块('..沙盒powershell.不变量',__name__)#旧包不变量
__all__=['包名','名称','依赖','安装','应用']
包名=源模块.包名
名称=源模块.名称
依赖=源模块.依赖
安装=源模块.安装
应用=源模块.应用
inject=依赖
name=名称
apply=应用
