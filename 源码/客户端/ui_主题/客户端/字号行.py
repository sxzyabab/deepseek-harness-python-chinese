import os
import pywebbridge
from ...ui_基础界面组件.icons import 图标上chevron14,图标下chevron14
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from ..主题设置 import 字号规格
from .文案 import 中文

__all__=['字号行']

class 字号行:
    '一个角色的字号：标题、说明、步进和 px'
    def __init__(自身,属性):
        '记下 props。槽位或字体设置组调用构造，键齐了就画。'
        自身.属性=属性
        自身.根=None
        if isinstance(属性,dict) and 'window' in 属性 and 'role' in 属性 and 'setFontSize' in 属性 and 'useStore' in 属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 渲染(自身):
        '拆掉旧行，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        角色=属性['role']
        注入模块样式文件(
            文档,
            '字号行样式',
            os.path.join(os.path.dirname(__file__),'字号行.module.css'),
            'font-size',
        )
        def 选字号(快照):
            '该角色已持久化的字号'
            return 快照['fontSizes'][角色]
        字号=属性['useStore'](选字号)
        规格=字号规格[角色]
        行=模块节点(文档,'div','font-size','row')
        文=模块节点(文档,'div','font-size','rowText')
        标题=模块节点(文档,'div','font-size','title')
        标题.textContent=中文['fontSize.'+角色+'.title']
        说明=模块节点(文档,'div','font-size','desc')
        说明.textContent=中文['fontSize.'+角色+'.description']
        文.appendChild(标题)
        文.appendChild(说明)
        行.appendChild(文)
        控=模块节点(文档,'div','font-size','control')
        丸=模块节点(文档,'div','font-size','stepper')
        值=模块节点(文档,'span','font-size','value')
        值.textContent=str(字号)
        箭=模块节点(文档,'span','font-size','arrows')
        加=模块节点(文档,'button','font-size','arrow')
        加.type='button'
        加.setAttribute('aria-label',中文['fontSize.'+角色+'.increase'])
        加.disabled=字号>=规格['max']
        图标上chevron14({'window':窗口,'size':9,'parent':加})
        def 加大(事件):
            '加一像素'
            属性['setFontSize'](字号+1)
        加.addEventListener('click',加大)
        减=模块节点(文档,'button','font-size','arrow')
        减.type='button'
        减.setAttribute('aria-label',中文['fontSize.'+角色+'.decrease'])
        减.disabled=字号<=规格['min']
        图标下chevron14({'window':窗口,'size':9,'parent':减})
        def 减小(事件):
            '减一像素'
            属性['setFontSize'](字号-1)
        减.addEventListener('click',减小)
        箭.appendChild(加)
        箭.appendChild(减)
        丸.appendChild(值)
        丸.appendChild(箭)
        控.appendChild(丸)
        单位=模块节点(文档,'span','font-size','unit')
        单位.textContent=中文['fontSize.unit']
        控.appendChild(单位)
        展开=属性.get('expander')
        if 展开 is not None:
            更多=模块节点(文档,'button','font-size','expander')
            更多.type='button'
            更多.setAttribute('aria-label',中文['fontSize.more'])
            更多.setAttribute('title',中文['fontSize.more'])
            更多.setAttribute('aria-expanded','true' if 展开['open'] else 'false')
            更多.setAttribute('aria-controls',展开['controls'])
            图标下chevron14({'window':窗口,'size':12,'parent':更多})
            def 点展开(事件):
                '展开或收起其余字体'
                展开['onToggle']()
            更多.addEventListener('click',点展开)
            控.appendChild(更多)
        行.appendChild(控)
        if 'parent' in 属性:
            属性['parent'].appendChild(行)
        自身.根=行
        return 自身.根

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
