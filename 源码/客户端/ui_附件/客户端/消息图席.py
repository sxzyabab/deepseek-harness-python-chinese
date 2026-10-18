'各处图片槽都画同一套图库。调用方没给文案时用对话命名空间的中文'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.客户端.文案 import 中文,填入
from ...ui_渲染器.客户端.作用域槽 import 拆除对象
from ..消息图 import 图库
from .标注列表 import 灯箱文案

__all__=['消息图内容','消息图席']

class 消息图内容:
    '官方图库。加载器由调用方授权，文案可以自带'
    def __init__(自身,属性):
        '记下图片列和布局，并画出图库'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.库=None
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换上新的图片列'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 拆除(自身):
        '卸掉图库里的加载和灯箱'
        if 自身.库 is not None:
            自身.库.拆除()
            自身.库=None

    def 渲染(自身):
        '有调用方文案就用它，否则用中文表。紧凑和缩略图缺省为否'
        属性=自身.属性
        文案=属性.get('labels')
        if not isinstance(文案,dict):
            def 具名打开(标签):
                '缩略图的无障碍名带上图片名'
                return 填入(中文['image.openOriginalLabel'],{'label':标签})
            文案={
                'image':中文['image.label'],
                'open':中文['image.openOriginal'],
                'openNamed':具名打开,
                'loading':中文['image.loading'],
                'loadFailed':中文['image.loadFailed'],
                'lightbox':灯箱文案(),
            }
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        库属性={
            'images':属性.get('images') or [],
            'load':属性.get('loadImage'),
            'align':属性.get('align'),
            'compact':属性.get('compact') is True,
            'thumbnail':属性.get('thumbnail') is True,
            'labels':文案,
            'window':窗口,
        }
        if 自身.库 is None:
            自身.库=图库(库属性)
        else:
            自身.库.更新(库属性)
            自身.库.渲染()
        自身.根=自身.库.根
        return 自身.根

class 消息图席:
    '消息、轨迹和工具图片位都转到同一套图库工厂'
    def __init__(自身,属性):
        '记下拥有方份额'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换上新的图片列'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 拆除(自身):
        '卸掉上一次工厂出现里的图库'
        if 自身.根 is not None:
            拆除对象(自身.根)
            自身.根=None

    def 渲染(自身):
        '只把拥有方给的图片、加载器和布局交给工厂'
        属性=自身.属性
        入={
            'images':属性.get('images'),
            'loadImage':属性.get('loadImage'),
            'align':属性.get('align'),
        }
        if 'compact' in 属性 and 属性['compact'] is not None:
            入['compact']=属性['compact']
        if 'thumbnail' in 属性 and 属性['thumbnail'] is not None:
            入['thumbnail']=属性['thumbnail']
        if 'window' in 属性:
            入['window']=属性['window']
        结果=属性['renderFactorySlot']('conversation.images.content',入)
        旧=自身.根
        if 旧 is not None and 旧 is not 结果:
            拆除对象(旧)
        if 旧 is not None and 旧 is not 结果 and getattr(旧,'parentNode',None) is not None:
            if 结果 is None:
                旧.remove()
            else:
                旧.parentNode.replaceChild(结果,旧)
        自身.根=结果
        return 结果
