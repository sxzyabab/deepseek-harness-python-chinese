from ..文案 import 中文
from .偏好行 import 偏好行

__all__=['链接打开行']


def 原样(值):
    '整份快照'
    return 值


class 链接打开行:
    '对话里网页链接的默认打开位置。内置浏览器没登记时这一行不出现'
    def __init__(自身,属性):
        '记下设置槽属性并画出。没有浏览器就不留节点'
        自身.属性=属性
        自身.行=None
        自身.根=None
        自身.已订=False
        自身.退订表=[]
        自身.渲染()

    def 选中(自身,值):
        '改默认打开位置'
        自身.属性['setLinkOpening'](值)

    def 渲染(自身):
        '浏览器不在时拆掉已画出的行'
        属性=自身.属性
        窗口=属性['window']
        目的地=属性['useLinkOpening'](原样)
        有浏览器=属性['useBrowserAvailable'](原样)
        if not 有浏览器:
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
                自身.行=None
            return None
        侧栏=目的地=='sidebar'
        行属性={
            'window':窗口,
            'title':中文['settings.links.title'],
            'description':中文['settings.links.description'],
            'value':目的地,
            'selectedLabel':中文['settings.links.sidebar'] if 侧栏 else 中文['settings.links.newTab'],
            'options':[
                {'id':'sidebar','label':中文['settings.links.sidebar']},
                {'id':'new-tab','label':中文['settings.links.newTab']},
            ],
            'onSelect':自身.选中,
        }
        if 自身.行 is None:
            if 'parent' in 属性:
                行属性['parent']=属性['parent']
            自身.行=偏好行(行属性)
            自身.根=自身.行.根
        else:
            自身.行.属性=行属性
            自身.行.渲染()
        if not 自身.已订:
            for 钩 in (属性['useLinkOpening'],属性['useBrowserAvailable']):
                订=getattr(钩,'_subscribe',None)
                if callable(订):
                    自身.退订表.append(订(自身.渲染))
            自身.已订=True
        return 自身.根
