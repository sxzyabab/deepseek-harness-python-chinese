import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from .文案 import 中文,填入

__all__=['当前版本行']

样式模块='currentVersion'

class 当前版本行:
    '构建写进页面的当前版本。没有版本号就不显示'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 渲染(自身):
        'DSH_CLIENT_VERSION 缺席时留空。有值则写成当前版本'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '当前版本行样式',
            os.path.join(os.path.dirname(__file__),'当前版本行.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        else:
            while 自身.根.firstChild is not None:
                自身.根.firstChild.remove()
        版本=os.environ.get('DSH_CLIENT_VERSION')
        if 版本 is None:
            return 自身.根
        行=文档.createElement('div')
        行.className='row'
        标样式模块(行,样式模块)
        行.textContent=填入(中文['general.currentVersion'],{'version':版本})
        自身.根.appendChild(行)
        return 自身.根
