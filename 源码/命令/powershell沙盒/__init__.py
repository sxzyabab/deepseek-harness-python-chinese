"""消费沙箱的 pwsh 执行器（中文名包）。

对齐上游 `@deepseek-ai/dsh-pwsh-sandbox`。实现见同组 `沙盒powershell`。
"""
from importlib import import_module as 导入模块#带连字符目录需经 importlib
_源=导入模块('..沙盒powershell',__name__)#旧包实现
__all__=list(_源.__all__)#公开面
for _名 in __all__:#逐项再导出
    globals()[_名]=getattr(_源,_名)#绑定
