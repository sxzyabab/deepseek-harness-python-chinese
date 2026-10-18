import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['常规条目分区']

样式模块='generalSection'

class 常规条目分区:
    '通用设置这一列，里面是各功能登记的条目'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 渲染(自身):
        '一列，子槽 settings.general.item'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '通用分区样式',
            os.path.join(os.path.dirname(__file__),'通用分区.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        自身.根.className='section'
        标样式模块(自身.根,样式模块)
        自身.根.appendChild(属性['renderSlot']('settings.general.item',{'window':窗口}))
        return 自身.根
