'收起时，对话标题角上的打开按钮'
from ....模块.客户端.通告 import 取握手窗口
import os
from ....ui_对话.异常 import 注入模块样式文件,标样式模块
from ....ui_基础界面组件.icons import 图标左栏16
from ....ui_基础界面组件.提示泡 import 提示泡
from ..文案 import 中文

__all__=['展开按钮']

样式路径=os.path.join(os.path.dirname(__file__),'展开按钮.module.css')
样式模块='sidebar-right-expand'


def _窗口(属性):
    '调用方带来的窗口，否则用桥上的窗口'
    if isinstance(属性,dict) and 属性.get('window') is not None:
        return 属性['window']
    return 取握手窗口()


def _订(钩子,回调):
    '选择器钩子上挂着的订阅'
    订=getattr(钩子,'_subscribe',None)
    if callable(订):
        return 订(回调)
    return None


class 展开按钮:
    '面板收起时显示。展开后这一席什么都不留'

    def __init__(自身,属性=None):
        '记下份额并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身._退订=[]
        自身.渲染()
        自身._订阅()

    def __call__(自身,属性=None):
        '再次绘制'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def _订阅(自身):
        '存储或快捷键变了就重画'
        def 变更():
            '还挂在页面上才重画'
            if 自身.根 is not None and getattr(自身.根,'isConnected',True) is False:
                自身._卸订()
                return
            自身.渲染()
        for 名 in ('useStore','useShortcuts'):
            钩=自身.属性.get(名)
            退=_订(钩,变更)
            if 退 is not None:
                自身._退订.append(退)

    def _卸订(自身):
        '摘掉订阅'
        for 退 in 自身._退订:
            退()
        自身._退订.clear()

    def 渲染(自身):
        '收起时是按钮，展开时拆掉'
        窗口=_窗口(自身.属性)
        文档=窗口.document
        注入模块样式文件(文档,'右侧展开按钮样式',样式路径,样式模块)
        会话标识=自身.属性.get('sessionId')
        用存储=自身.属性.get('useStore')
        展开=False
        if callable(用存储):
            def 取展开(状态):
                '这一会话的展开位。还没有表面就算收起'
                表面=状态['bySession'].get(会话标识)
                if 表面 is None:
                    return False
                return 表面['layout']['expanded'] is True
            展开=用存储(取展开) is True
        if 展开:
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            return 自身
        快捷=None
        用快捷=自身.属性.get('useShortcuts')
        if callable(用快捷):
            def 取切换(条目表):
                '展开收起那条'
                for 行 in 条目表:
                    if 行.get('id')=='sidebar.right.toggle':
                        return 行
                return None
            快捷=用快捷(取切换)
        动作=自身.属性.get('actions') or {}

        def 点击():
            '展开这一会话'
            动作['设展开'](会话标识,True)

        钮=文档.createElement('button')
        钮.type='button'
        钮.className='button'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-label',中文['chrome.expandAria'])
        钮.setAttribute('data-sidebar-right-expand','')
        if 快捷 is not None and 快捷.get('aria'):
            钮.setAttribute('aria-keyshortcuts',快捷['aria'])
        钮.addEventListener('click',lambda 事件: 点击())
        图=图标左栏16({'window':窗口,'className':'icon'})
        if 图 is not None:
            标样式模块(图,样式模块)
            钮.appendChild(图)
        提示文=中文['chrome.expand']
        if 快捷 is not None and 快捷.get('keys'):
            提示文=提示文+' '+' '.join(str(键) for 键 in 快捷['keys'])
        泡=提示泡({'window':窗口,'label':提示文,'side':'bottom','children':钮})
        自身.根=泡.渲染()
        父=自身.属性.get('parent')
        if 父 is not None and 自身.根 is not None and getattr(自身.根,'parentNode',None) is None:
            父.appendChild(自身.根)
        return 自身
