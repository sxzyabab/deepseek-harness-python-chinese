"""`@deepseek-ai/dsh-pwsh-sandbox` 的本包拥有不变量配套（中文名包）。"""
from importlib import import_module as 导入模块#带连字符目录需经 importlib
源模块=导入模块('..沙盒powershell.不变量',__name__)#旧包不变量
__all__=['包名','名称','注入','安装','应用']#仅中文公开名
包名=源模块.包名#再导出
名称=源模块.名称#再导出
注入=源模块.注入#再导出
安装=源模块.安装#再导出
应用=源模块.应用#再导出
