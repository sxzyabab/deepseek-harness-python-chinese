'浏览器入口：挂上桥的 Remote，并在提示上方登记条带'
from .挂载 import 依赖,挂载模组条带
from .条带 import 条带
from .文案 import 命名空间,中文,英文

__all__=['依赖','应用','挂载模组条带','命名空间','中文','英文','条带']

远程贡献={
    'package':'@deepseek-ai/dsh-experimental-claude-code-mods',
    'namespace':'claudeCodeMods',
}

def 应用(上下文):
    '在客户端上下文登记模组条带。返回卸除期约'
    return 挂载模组条带(上下文,远程贡献)

inject=依赖
apply=应用
