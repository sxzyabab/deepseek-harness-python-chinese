import os
import pywebbridge
from ...ui_基础界面组件.输入 import 输入
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from ..主题设置 import 规范化字体族
from .文案 import 中文

__all__=['字体族行']

class 字体族行:
    '一个角色的字体列表。失焦或回车后规范化再写入，空串恢复内置栈'
    def __init__(自身,属性):
        '记下 props。键齐了就画。'
        自身.属性=属性
        自身.根=None
        if isinstance(属性,dict) and 'window' in 属性 and 'role' in 属性 and 'setFontFamily' in 属性 and 'useStore' in 属性:
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
        注入模块样式文件(
            文档,
            '字体族行样式',
            os.path.join(os.path.dirname(__file__),'字体族行.module.css'),
            'font-family',
        )
        def 选列表(快照):
            '该角色已持久化的字体列表'
            return 快照['fontFamilies'][角色]
        列表=属性['useStore'](选列表)
        标题文=中文['fontFamily.'+角色+'.title']
        行=模块节点(文档,'div','font-size','row')
        文=模块节点(文档,'div','font-size','rowText')
        标题=模块节点(文档,'div','font-size','title')
        标题.textContent=标题文
        说明=模块节点(文档,'div','font-size','desc')
        说明.textContent=中文['fontFamily.'+角色+'.description']
        文.appendChild(标题)
        文.appendChild(说明)
        行.appendChild(文)
        壳=输入({
            'window':窗口,
            'className':'field',
            'value':列表,
            'placeholder':中文['fontFamily.placeholder'],
        }).渲染()
        壳.setAttribute('data-dsh-css','font-family')
        框=壳.querySelector('input')
        框.setAttribute('aria-label',标题文)
        框.setAttribute('spellcheck','false')
        框.setAttribute('autocomplete','off')
        框.maxLength=200
        def 失焦(事件):
            '规范化后写入。空串恢复内置栈'
            输入框=事件.currentTarget
            输入框.value=规范化字体族(输入框.value)
            属性['setFontFamily'](输入框.value)
        框.addEventListener('blur',失焦)
        def 按下(事件):
            '组合输入不提交；回车让输入框失焦'
            if 事件.isComposing or 事件.keyCode==229:
                return
            if 事件.key=='Enter':
                事件.currentTarget.blur()
        框.addEventListener('keydown',按下)
        行.appendChild(壳)
        if 'parent' in 属性:
            属性['parent'].appendChild(行)
        自身.根=行
        return 自身.根

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
