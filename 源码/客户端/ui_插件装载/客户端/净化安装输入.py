import re

__all__=['净化安装输入']

包名形态=re.compile(r'^(?:@[a-z0-9._-]+/)?[a-z0-9][a-z0-9._-]*(?:@[a-z0-9.*^~+<>=| -]+)?$',re.IGNORECASE)
地址形态=re.compile(r'^(?:git[+:]|git@|github:|gitlab:|bitbucket:)',re.IGNORECASE)
网址形态=re.compile(r'^[a-z][a-z0-9+.-]*://',re.IGNORECASE)

def 净化安装输入(规格):
    '保留注册表包名和普通版本。其余只留下种类，不带地址、凭据或本机路径'
    if 包名形态.match(规格) is not None:
        return 规格
    if 地址形态.match(规格) is not None:
        return '[git]'
    if 网址形态.match(规格) is not None:
        return '[url]'
    return '[path-or-other]'
