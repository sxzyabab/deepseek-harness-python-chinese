from .挂载 import 依赖,挂载语音输入
from .文案 import 命名空间,中文,英文
from .语音输入安装对话框 import 语音输入安装对话框
from ...api_语音转写 import 远程贡献
from . import (
    准备卡片,
    就绪度,
    波形图,
    语音输入,
    语音输入安装提示,
    音频,
)

__all__=['依赖','应用','挂载语音输入','命名空间','中文','英文','语音输入安装对话框']

def 应用(上下文):
    '挂上生成的 speech Remote 与浏览器控件'
    return 挂载语音输入(上下文,远程贡献)

inject=依赖
apply=应用
