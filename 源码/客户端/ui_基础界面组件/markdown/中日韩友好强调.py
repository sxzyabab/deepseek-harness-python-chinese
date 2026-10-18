import unicodedata

__all__=['是中日韩字符','中日韩可关闭','中日韩友好强调']

def 是中日韩字符(码):
    '码点属于汉字、平假名、片假名、谚文或注音'
    if not isinstance(码,int) or 码<0:
        return False
    if 0x3400<=码<=0x4DBF or 0x4E00<=码<=0x9FFF or 0xF900<=码<=0xFAFF:
        return True
    if 0x3040<=码<=0x30FF:
        return True
    if 0xAC00<=码<=0xD7AF:
        return True
    if 0x3100<=码<=0x312F:
        return True
    return False

def 中日韩可关闭(前一个,后一个,标记数):
    '两个以上星号，前一个是标点，后一个是中日韩字符，就可以关闭强调'
    if not isinstance(标记数,int) or 标记数<2:
        return False
    if not isinstance(前一个,str) or 前一个=='':
        return False
    if not unicodedata.category(前一个).startswith('P'):
        return False
    return 是中日韩字符(后一个)

def 中日韩友好强调():
    '星号强调在中日韩标点后仍可关闭。micromark 扩展对象不在这棵树里，这里登记构造名'
    return {'text':{'asterisk':'cjkFriendlyAttention'}}
