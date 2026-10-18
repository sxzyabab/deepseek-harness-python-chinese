import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from .字号行 import 字号行
from .字体族行 import 字体族行

__all__=['字体设置组']

class 字体设置组:
    '正文字号，展开后是三种字体以及代码、终端字号。每次新建都收起'
    def __init__(自身,属性):
        '记下 props。每次新建都从收起开始，键齐了就画。'
        自身.属性=属性
        自身.根=None
        自身.展开=False
        自身.区域标识='font-settings-'+str(id(自身))
        if isinstance(属性,dict) and 'window' in 属性 and 'setFontSize' in 属性 and 'setFontFamily' in 属性 and 'useStore' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新。展开状态留在这一实例上'
        自身.属性=属性

    def 渲染(自身):
        '拆掉旧组，再画一次'
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '字体设置组样式',
            os.path.join(os.path.dirname(__file__),'字体设置组.module.css'),
            'font-settings',
        )
        共用={'window':窗口,'useStore':属性['useStore']}
        def 切换():
            '展开或收起其余字体'
            自身.展开=not 自身.展开
            自身.渲染()
        def 字体行(角色):
            '该角色的字体列表行'
            def 写入(值,某=角色):
                '写入该角色的字体列表'
                属性['setFontFamily'](某,值)
            return 字体族行({**共用,'role':角色,'setFontFamily':写入}).渲染()
        def 字号(角色,展开=None):
            '该角色的字号行'
            def 写入(像素,某=角色):
                '写入该角色的字号'
                属性['setFontSize'](某,像素)
            材料={**共用,'role':角色,'setFontSize':写入}
            if 展开 is not None:
                材料['expander']=展开
            return 字号行(材料).渲染()
        组=模块节点(文档,'div','font-settings','group')
        组.appendChild(字号('text',{
            'open':自身.展开,
            'controls':自身.区域标识,
            'onToggle':切换,
        }))
        if 自身.展开:
            区域=文档.createElement('div')
            区域.id=自身.区域标识
            区域.appendChild(字体行('text'))
            区域.appendChild(字体行('code'))
            区域.appendChild(字号('code'))
            区域.appendChild(字体行('terminal'))
            区域.appendChild(字号('terminal'))
            组.appendChild(区域)
        if 父 is not None:
            父.appendChild(组)
        elif 'parent' in 属性:
            属性['parent'].appendChild(组)
        自身.根=组
        return 自身.根

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
