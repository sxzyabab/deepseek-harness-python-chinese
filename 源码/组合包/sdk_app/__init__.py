"""SDK profile 的命令行与 stdin 生命周期提供方（中文名包）。

对齐上游 `@deepseek-ai/dsh-sdk-app`。实现见同组 `sdk-app`。
"""
from importlib import import_module as 导入模块#带连字符目录需经 importlib
_源=导入模块('..sdk-app',__name__)#旧包实现
__all__=list(_源.__all__)#公开面
for _名 in __all__:#逐项再导出
    globals()[_名]=getattr(_源,_名)#绑定
