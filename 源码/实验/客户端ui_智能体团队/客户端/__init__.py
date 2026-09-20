from .挂载 import 依赖,挂载智能体团队界面,登记界面
from .团队动作 import 团队动作
from .文案 import 命名空间,中文,英文

__all__=[
    '依赖','应用','挂载智能体团队界面','团队动作',
    '命名空间','中文','英文',
]

def 应用(上下文,远程制品=None):
    """挂载生成的 Team Remote contribution 及其浏览器 UI。"""
    if 远程制品 is None:
        return 登记界面(上下文)
    return 挂载智能体团队界面(上下文,远程制品)

inject=依赖
apply=应用
