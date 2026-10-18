__all__=['不换行图标16','换行图标16','处理不换行图标','处理换行图标']

_不换行路径='M1.5 2.5H3.5V21.5H1.5V2.5ZM20.5 2.5H22.5V21.5H20.5V2.5ZM14 9L19 12L14 15V13H5V11H14V9Z'
_换行路径='M1.5 2.5H3.5V21.5H1.5V2.5ZM20.5 2.5H22.5V21.5H20.5V2.5ZM6.75 5H11.5A6 6 0 0 1 12 16.98V19L7 16L12 13V14.97A4 4 0 0 0 11.5 7H6.75V5Z'


def _画字形(文档,尺寸,类名,路径):
    '把二十四视口字形画成 svg'
    宽=尺寸 if isinstance(尺寸,int) else 16
    节=文档.createElement('span')
    if isinstance(类名,str) and 类名!='':
        节.className=类名
    节.innerHTML=(
        '<svg width="'+str(宽)+'" height="'+str(宽)+'" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
        '<path d="'+路径+'"/>'
        '</svg>'
    )
    return 节

def 处理不换行图标(window,属性):
    '画出不换行字形。有 parent 就挂上去'
    尺寸=属性['尺寸'] if isinstance(属性,dict) and '尺寸' in 属性 else 16
    类名=属性['类名'] if isinstance(属性,dict) and '类名' in 属性 else None
    节=_画字形(window.document,尺寸,类名,_不换行路径)
    if isinstance(属性,dict) and 'parent' in 属性:
        属性['parent'].appendChild(节)
    return 节

def 处理换行图标(window,属性):
    '画出换行字形。有 parent 就挂上去'
    尺寸=属性['尺寸'] if isinstance(属性,dict) and '尺寸' in 属性 else 16
    类名=属性['类名'] if isinstance(属性,dict) and '类名' in 属性 else None
    节=_画字形(window.document,尺寸,类名,_换行路径)
    if isinstance(属性,dict) and 'parent' in 属性:
        属性['parent'].appendChild(节)
    return 节


class 不换行图标16:
    '两边距条，直箭头指向右侧：行越过边缘'

    def __init__(自身,尺寸=16,类名=None):
        '记下边长与类名。预览工具条会调用渲染，这里不重复画'
        自身.尺寸=尺寸
        自身.类名=类名
        自身.window=None
        自身.根=None

    def 渲染(自身):
        '拆掉旧字形，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        if 自身.window is None:
            自身.根=None
            return None
        自身.根=处理不换行图标(自身.window,{'尺寸':自身.尺寸,'类名':自身.类名})
        return 自身.根


class 换行图标16:
    '两边距条，箭头绕回左侧：行折到自身下方'

    def __init__(自身,尺寸=16,类名=None):
        '记下边长与类名。预览工具条会调用渲染，这里不重复画'
        自身.尺寸=尺寸
        自身.类名=类名
        自身.window=None
        自身.根=None

    def 渲染(自身):
        '拆掉旧字形，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        if 自身.window is None:
            自身.根=None
            return None
        自身.根=处理换行图标(自身.window,{'尺寸':自身.尺寸,'类名':自身.类名})
        return 自身.根
