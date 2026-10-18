from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.icons import 图标Cordis插件14

__all__=['插件面板图标']

class 插件面板图标:
    '侧栏插件入口的字形。按钮、标签和选中态由侧栏拥有'
    def __init__(自身,属性):
        '记下侧栏交来的边长，并画出字形'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '边长变了就重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '按侧栏要的边长画插件字形'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        图属性={'window':窗口}
        if 'size' in 属性:
            图属性['size']=属性['size']
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
        根=图标Cordis插件14(图属性)
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and 根 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
