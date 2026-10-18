import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标设置16
from .文案 import 中文

__all__=['触发内容','页眉内容','关闭标签']

样式模块='chrome'

class 触发内容:
    '触发器里的设置图标。宽栏才带「设置」'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 渲染(自身):
        '宽栏 16、窄栏 18。窄栏不放文字'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '壳层样式',
            os.path.join(os.path.dirname(__file__),'壳层.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        宽=属性.get('wide') is True
        尺寸=16 if 宽 else 18
        自身.根.appendChild(图标设置16({'window':窗口,'size':尺寸}))
        if 宽:
            字=模块节点(文档,'span',样式模块,'triggerLabel')
            字.textContent=中文['trigger']
            自身.根.appendChild(字)
        return 自身.根

class 页眉内容:
    '面板标题，原文是设置'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 渲染(自身):
        '标题文本'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('span')
        自身.根.textContent=中文['title']
        return 自身.根

class 关闭标签:
    '关闭按钮里视觉上隐藏的名字，原文是关闭'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 渲染(自身):
        '关闭二字'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('span')
        自身.根.textContent=中文['close']
        return 自身.根
