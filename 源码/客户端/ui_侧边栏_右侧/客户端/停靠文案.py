'交给停靠套件显示的字。这里用中文表原文，不走文案函数'
from .文案 import 中文

__all__=['停靠标签']


def 停靠标签(翻译=None,分栏键=None,关闭键=None):
    '套件要的全部文案。翻译参数留下是为了对上旧调用，显示不读它'
    return {
        'emptyPane':中文['dock.emptyPane'],
        'splitPane':中文['dock.splitPane'],
        'splitPaneShortcut':None if 分栏键 is None else 分栏键.get('aria'),
        'splitPaneKeys':None if 分栏键 is None else 分栏键.get('keys'),
        'splitPaneDisabled':中文['dock.splitPaneDisabled'],
        'splitPaneNarrow':中文['dock.splitPaneNarrow'],
        'closeTab':中文['dock.closeTab'],
        'closeTabShortcut':None if 关闭键 is None else 关闭键.get('aria'),
        'closeTabKeys':None if 关闭键 is None else 关闭键.get('keys'),
        'addTab':中文['dock.addTab'],
        'dockFloat':中文['dock.dockFloat'],
        'closeFloat':中文['dock.closeFloat'],
        'dropZone':{
            'center':中文['dock.drop.center'],
            'left':中文['dock.drop.left'],
            'right':中文['dock.drop.right'],
            'top':中文['dock.drop.top'],
            'bottom':中文['dock.drop.bottom'],
        },
    }
