from .挂载 import 依赖,挂载语音输入
from .文案 import 命名空间,中文,英文
from ...api_语音转写 import 远程贡献

__all__=['依赖','应用','挂载语音输入','命名空间','中文','英文']

def 应用(上下文):
    """挂上生成的 speech Remote 与浏览器控件。"""
    return 挂载语音输入(上下文,远程贡献)

inject=依赖
apply=应用
