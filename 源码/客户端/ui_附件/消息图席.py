'消息图片槽的图库入口'
from .消息图 import 图库

__all__=['消息图席','消息图文案']

def 消息图文案(翻译):
    '历史图片和灯箱用的句子'
    return {
        'image':翻译('image.label'),
        'open':翻译('image.openOriginal'),
        'openNamed':lambda 标签:翻译('image.openOriginalLabel',{'label':标签}),
        'loading':翻译('image.loading'),
        'loadFailed':翻译('image.loadFailed'),
        'lightbox':{'dialog':翻译('image.preview'),'close':翻译('image.closePreview')},
    }

class 消息图席:
    '把槽位上的 images、loadImage 和文案交给图库。槽位只调用构造，键齐了就画'
    def __init__(自身,属性):
        '记下 props。图库由渲染画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.库=图库(自身.库属性())
        if 'images' in 自身.属性:
            自身.渲染()

    def 翻译(自身):
        '缺文案钩子时返回键'
        翻译=自身.属性.get('t')
        if callable(翻译):
            return 翻译
        return lambda 键,参数=None:键

    def 库属性(自身):
        '对齐 MessageImages 的字段名'
        图列=自身.属性.get('images')
        return {
            'images':图列 if isinstance(图列,list) else [],
            'load':自身.属性.get('loadImage'),
            'align':自身.属性.get('align'),
            'compact':自身.属性.get('compact') is True,
            'thumbnail':自身.属性.get('thumbnail') is True,
            'labels':消息图文案(自身.翻译()),
        }

    def 更新(自身,属性):
        '刷新并重建图库'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.库.更新(自身.库属性())

    def 渲染(自身):
        '空图列不画'
        自身.库.更新(自身.库属性())
        return 自身.库.渲染()

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
