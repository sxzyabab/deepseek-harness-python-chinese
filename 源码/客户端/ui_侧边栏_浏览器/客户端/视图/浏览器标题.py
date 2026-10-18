import pywebbridge
from ....ui_基础界面组件.icons import 图标地球14
from ..浏览器.浏览器持久化 import 当前浏览器目标
from .浏览器呈现形式 import 取窗口,确保浏览器样式,标浏览器

__all__=['浏览器标题']


class 浏览器标题:
    '地球图标和当前主机名。没有主机名时用签上原来的标题'
    按标签={}

    def __new__(类,属性=None):
        '同一张签复用一份标题，返回根节点'
        信息=属性['useTabInfo']()
        标识=信息['tab']['id']
        已有=类.按标签.get(标识)
        if 已有 is not None:
            已有.属性=属性
            已有.渲染()
            return 已有.根
        自身=object.__new__(类)
        自身.标签标识=标识
        自身.__init__(属性)
        类.按标签[标识]=自身
        return 自身.根

    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.窗口=取窗口(属性)
        自身.根=None
        自身.退订=None
        自身.文字=None
        信号=None
        信息=属性['useTabInfo']()
        签=信息.get('tab') if isinstance(信息,dict) else None
        if isinstance(签,dict):
            信号=签.get('signal')

        def 签结束():
            '签结束就放下标题'
            浏览器标题.按标签.pop(自身.标签标识,None)
            if callable(自身.退订):
                自身.退订()
                自身.退订=None

        if 信号 is not None and hasattr(信号,'addEventListener'):
            信号.addEventListener('abort',签结束,{'once':True})
        用存储=属性.get('useStore')
        if callable(用存储) and callable(getattr(用存储,'_subscribe',None)):
            def 变更():
                '保存的地址变了就重画'
                自身.渲染()
            自身.退订=用存储._subscribe(变更)
        自身.渲染()

    def 渲染(自身):
        '读存储里的当前主机名'
        文档=自身.窗口.document
        确保浏览器样式(文档)
        信息=自身.属性['useTabInfo']()
        签=信息['tab']

        def 取条目(状态):
            '这一签当前地址'
            按签=状态.get('byTab') if isinstance(状态,dict) else None
            if not isinstance(按签,dict):
                return None
            return 当前浏览器目标(按签.get(签['id']))

        条目=自身.属性['useStore'](取条目)
        标题=签.get('title') if isinstance(签,dict) else ''
        if 条目 is not None and 条目.get('title') is not None:
            标题=条目['title']
        if 自身.根 is None:
            根=文档.createElement('span')
            根.style.display='contents'
            图=图标地球14({'window':自身.窗口,'className':'titleIcon'})
            if 图 is not None:
                标浏览器(图,'titleIcon')
                根.appendChild(图)
            文字=文档.createElement('span')
            根.appendChild(文字)
            自身.根=根
            自身.文字=文字
        自身.文字.textContent=标题 if 标题 is not None else ''
        return 自身.根
