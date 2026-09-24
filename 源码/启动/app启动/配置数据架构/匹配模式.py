"""原生正则校验与 Unicode JSON Schema 模式之间的保守兼容检查。"""
import re

__all__=['创建模式检查']

偶发键=frozenset(('parent','start','end','raw','references','resolved'))

def 可移植源(源,标志=''):
    """不执行正则，只判断能否作为标准 pattern 约束。"""
    if 标志!='' and 标志!='u':
        return False
    try:
        re.compile(源)
    except re.error:
        return False
    if 标志=='u':
        return True
    if re.search(r'\\[pP]|\\u\{|\\x\{',源) is not None:
        return False
    return True

def 创建模式检查():
    """返回兼容谓词；解析从不对配置值执行正则。"""
    return 可移植源
