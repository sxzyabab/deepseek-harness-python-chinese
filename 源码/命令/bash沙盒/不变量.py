"""`@deepseek-ai/dsh-bash-sandbox` 的本包拥有不变量配套（中文名包）。"""
from importlib import import_module as 导入模块#带连字符目录需经 importlib
_源=导入模块('..沙盒bash.不变量',__name__)#旧包不变量
__all__=['包名','名称','注入','安装','应用']#仅中文公开名
包名=_源.包名#再导出
名称=_源.名称#再导出
注入=_源.注入#再导出
安装=_源.安装#再导出
应用=_源.应用#再导出
