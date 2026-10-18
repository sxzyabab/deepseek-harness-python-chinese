from .icons import 常规描边,中等描边
from .icons.共享画稿 import 聊天线描边画稿,浏览描边画稿,关文件夹画稿

__all__=['引用图标常规','引用图标中等']

def 引用画稿(属性,描边宽):
    'session 用聊天线，file 用浏览，folder 用合上的文件夹'
    合成=属性 if isinstance(属性,dict) else {}
    种类=合成.get('kind')
    if 种类=='session':
        return 聊天线描边画稿(合成,描边宽)
    if 种类=='file':
        return 浏览描边画稿(合成,描边宽)
    if 种类=='folder':
        return 关文件夹画稿(合成,描边宽)
    raise ValueError('unreachable reference icon kind: '+str(种类))

def 引用图标常规(属性=None):
    '一像素引用图标'
    return 引用画稿(属性,常规描边)

def 引用图标中等(属性=None):
    '1.3 引用图标'
    return 引用画稿(属性,中等描边)
