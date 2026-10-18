import os
from ....ui_对话.异常 import 注入模块样式文件,模块节点
from ....ui_基础界面组件.icons import 图标下箭头描边常规
from ....ui_基础界面组件.菜单 import 菜单

__all__=['偏好行']

样式模块='PreferenceRow'
样式路径=os.path.join(os.path.dirname(__file__),'偏好行.module.css')


class 偏好行:
    '设置行：左侧标题说明，右侧菜单。选中后先把焦点还给按钮，再公布新值'
    def __init__(自身,属性):
        '记下文案、当前值和选项，并画出这一行'
        自身.属性=属性
        自身.开=False
        自身.选择钮=None
        自身.根=None
        自身.菜单=None
        自身.标题节点=None
        自身.说明节点=None
        自身.渲染()

    def 关闭(自身):
        '关掉菜单'
        自身.开=False
        自身.渲染()

    def 选中(自身,标识):
        '先把焦点还给按钮，再关菜单，最后把新值交出去'
        if 自身.选择钮 is not None:
            自身.选择钮.focus()
        自身.开=False
        自身.属性['onSelect'](标识)
        自身.渲染()

    def 切换(自身,事件=None):
        '点按钮开关菜单'
        自身.开=not 自身.开
        自身.渲染()

    def 渲染(自身):
        '标题、说明和当前标签就地改。菜单按打开状态重画'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(文档,'dsh-chat-preference-row',样式路径,样式模块)
        if 自身.根 is None:
            自身.根=模块节点(文档,'div',样式模块,'row')
            文区=模块节点(文档,'div',样式模块,'rowText')
            自身.标题节点=模块节点(文档,'div',样式模块,'title')
            自身.说明节点=模块节点(文档,'div',样式模块,'desc')
            文区.appendChild(自身.标题节点)
            文区.appendChild(自身.说明节点)
            自身.选择钮=模块节点(文档,'button',样式模块,'selector')
            自身.选择钮.setAttribute('type','button')
            自身.选择钮.setAttribute('aria-haspopup','menu')
            自身.选择钮.addEventListener('click',自身.切换)
            自身.根.appendChild(文区)
            自身.根.appendChild(自身.选择钮)
            if 'parent' in 属性 and 属性['parent'] is not None:
                属性['parent'].appendChild(自身.根)
        自身.标题节点.textContent=属性['title']
        自身.说明节点.textContent=属性['description']
        自身.选择钮.setAttribute('aria-expanded','true' if 自身.开 else 'false')
        while 自身.选择钮.firstChild is not None:
            自身.选择钮.removeChild(自身.选择钮.firstChild)
        自身.选择钮.appendChild(文档.createTextNode(属性['selectedLabel']))
        图标下箭头描边常规({
            'window':窗口,
            'className':'chevron',
            'parent':自身.选择钮,
        })
        自身.选择钮.lastChild.setAttribute('data-dsh-css',样式模块)
        if 自身.菜单 is None:
            自身.菜单=菜单({
                'window':窗口,
                'open':自身.开,
                'onClose':自身.关闭,
                'items':属性['options'],
                'selectedId':属性['value'],
                'onSelect':自身.选中,
                'align':'end',
                'portal':True,
                'anchor':自身.选择钮,
            })
        else:
            自身.菜单.更新({
                'window':窗口,
                'open':自身.开,
                'onClose':自身.关闭,
                'items':属性['options'],
                'selectedId':属性['value'],
                'onSelect':自身.选中,
                'align':'end',
                'portal':True,
                'anchor':自身.选择钮,
            })
        自身.菜单.渲染()
        return 自身.根
