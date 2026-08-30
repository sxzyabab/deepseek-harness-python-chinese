"""组：技能。"""
from importlib import import_module as 导入模块
from . import (
    工具_技能,
    技能,
    技能徽章,
)
globals()['技能-文件系统']=导入模块('.技能-文件系统',__name__)
__all__=[
    '工具_技能',
    '技能',
    '技能-文件系统',
    '技能徽章',
]
