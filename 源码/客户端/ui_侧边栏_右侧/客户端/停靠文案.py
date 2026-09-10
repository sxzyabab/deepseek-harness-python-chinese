"""停靠套件词表：把本包词典投影成套件标签契约。

对齐上游 `ui-sidebar-right/src/client/labels.ts`。公开面仅中文名。
套件不自持文案；渲染时调用，语言切换在下一帧到达套件。
"""

__all__=['停靠标签']#仅中文公开名


def 停靠标签(翻译):
    """把命名空间绑定翻译投影为停靠套件文案 dict。"""
    return {#套件标签契约（键为线协议英文）
        'emptyPane':翻译('dock.emptyPane'),#空面板
        'splitPane':翻译('dock.splitPane'),#分栏
        'splitPaneDisabled':翻译('dock.splitPaneDisabled'),#已满
        'splitPaneNarrow':翻译('dock.splitPaneNarrow'),#过窄
        'closeTab':翻译('dock.closeTab'),#关签
        'addTab':翻译('dock.addTab'),#加签
        'dockFloat':翻译('dock.dockFloat'),#收回
        'closeFloat':翻译('dock.closeFloat'),#关浮
        'dropZone':{#投放区
            'center':翻译('dock.drop.center'),#中心
            'left':翻译('dock.drop.left'),#左
            'right':翻译('dock.drop.right'),#右
            'top':翻译('dock.drop.top'),#上
            'bottom':翻译('dock.drop.bottom'),#下
        },
    }#投影结束
