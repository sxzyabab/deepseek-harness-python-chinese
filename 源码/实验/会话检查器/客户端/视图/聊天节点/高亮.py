'检查器元素选取蒙层在 Chat 子树之外的裁剪几何'

from .文档对象 import 矩形字典

__all__=['可见聊天矩形','放置聊天高亮']

def 写样式(元素,表):
    '把几何写到固定定位元素上'
    样式=元素.style
    for 键,值 in 表.items():
        if isinstance(样式,dict):
            样式[键]=值
        else:
            setattr(样式,键,值)

def 可见聊天矩形(元素):
    'Chat 盒与滚动口、composer 上方记录区的交集'
    矩形=矩形字典(元素.getBoundingClientRect())
    左=max(0,矩形['left'])
    右=min(window.innerWidth,矩形['right'])
    上=max(0,矩形['top'])
    下=min(window.innerHeight,矩形['bottom'])
    父=元素.parentElement
    while 父 is not None:
        if 父.matches('[data-conversation-scroll], [data-step-process-body]'):
            界=矩形字典(父.getBoundingClientRect())
            左=max(左,界['left'])
            右=min(右,界['right'])
            上=max(上,界['top'])
            下=min(下,界['bottom'])
            if 父.hasAttribute('data-conversation-scroll'):
                座位=父.querySelector(':scope > [data-composer-seat]')
                if 座位 is not None:
                    作曲=矩形字典(座位.getBoundingClientRect())
                    if 作曲['height']>0:
                        下=min(下,作曲['top'])
        父=父.parentElement
    if 下<=上 or 右<=左:
        return None
    return {'left':左,'top':上,'width':右-左,'height':下-上}

def 放置聊天高亮(覆盖层,元素):
    '放置检查器覆盖层，不改变 Chat 内容盒'
    矩形=可见聊天矩形(元素)
    if 矩形 is None:
        return False
    写样式(覆盖层,{
        'left':f"{矩形['left']}px",
        'top':f"{矩形['top']}px",
        'width':f"{矩形['width']}px",
        'height':f"{矩形['height']}px",
    })
    return True
