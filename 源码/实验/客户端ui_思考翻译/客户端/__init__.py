from .挂载 import 依赖,挂载思考翻译
from .文案 import 命名空间,中文,英文
from .. import 远程贡献

__all__=['依赖','应用','挂载思考翻译','命名空间','中文','英文']

def 应用(上下文):
    '挂上实验思考翻译展示与其 Remote。返回期约，兑现值是卸除函数'
    return 挂载思考翻译(上下文,远程贡献)

inject=依赖
apply=应用
