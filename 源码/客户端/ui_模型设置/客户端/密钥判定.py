import re

__all__=['密钥失败']

合法密钥模式=re.compile(r'^[\x21-\x7E]+\Z')
环境行模式=re.compile(r'^[A-Z][A-Z0-9_]*=[^=]')

def 密钥失败(草稿):
    '空字段表示沿用已存密钥。只含空白、环境赋值行、引号包裹或非可打印字符则返回文案键'
    if len(草稿)==0:
        return None
    值=草稿.strip()
    if len(值)==0:
        return 'keyBlank'
    首=值[0]
    引号包裹=False
    if 首=='"' or 首=="'" or 首=='`':
        引号包裹=len(值)>1 and 值.endswith(首)
    if 环境行模式.match(值) is not None or 引号包裹:
        return 'keyIllegalCharacters'
    if 合法密钥模式.match(值) is None:
        return 'keyIllegalCharacters'
    return None
