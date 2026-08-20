"""再导出：提示词模块入口对齐 `提示.py`。

对齐上游 `prompt.ts`；正文见 `./提示`。
"""
from .提示 import cordis系统提示#系统提示词

Cordis系统提示词=cordis系统提示#别名
CORDIS_SYSTEM_PROMPT=cordis系统提示#上游常量名

__all__=['cordis系统提示','Cordis系统提示词','CORDIS_SYSTEM_PROMPT']#公开面
