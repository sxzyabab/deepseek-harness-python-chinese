"""组：交互。"""
from importlib import import_module as 导入模块
from . import (
    指令,
    用户审批,
    用户提问,
    权限预设,
)
globals()['工具-询问用户']=导入模块('.工具-询问用户',__name__)
__all__=[
    '工具-询问用户',
    '指令',
    '用户审批',
    '用户提问',
    '权限预设',
]
