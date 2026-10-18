import os
from ....ui_基础界面组件.icons import 图标下chevron14
from ...异常 import 注入模块样式文件,标样式模块

__all__=['回车行为行']

样式模块='enter-behavior-row'

class 回车行为行:
    '繁忙时 Enter 和发送按钮走排队还是插话'
    def __init__(自身,属性):
        '菜单默认关着'
        自身.属性=属性
        自身.根=None
        自身.开=False
        自身.已订=False
        自身.渲染()

    def 渲染(自身):
        '标题、说明，以及当前行为的菜单'
        from ....ui_基础界面组件.菜单 import 菜单#菜单表面会回头导入本包，顶层导入会成环
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '回车行为行样式',
            os.path.join(os.path.dirname(__file__),'回车行为行.module.css'),
            样式模块,
        )
        行为=属性['useBusyEnter'](lambda 值:值)
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        elif 'parent' in 属性:
            父=属性['parent']
        行=文档.createElement('div')
        行.className='row'
        标样式模块(行,样式模块)
        文=文档.createElement('div')
        文.className='rowText'
        标样式模块(文,样式模块)
        题=文档.createElement('div')
        题.className='title'
        标样式模块(题,样式模块)
        题.textContent='繁忙时的发送行为'
        述=文档.createElement('div')
        述.className='desc'
        标样式模块(述,样式模块)
        述.textContent='智能体运行时 Enter 键和发送按钮的行为；Cmd/Ctrl+Enter 使用另一行为'
        文.appendChild(题)
        文.appendChild(述)
        行.appendChild(文)
        当前='排队发送' if 行为=='queue' else '插话发送'
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='selector'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-haspopup','menu')
        钮.setAttribute('aria-expanded','true' if 自身.开 else 'false')
        钮.textContent=当前
        箭=图标下chevron14({'window':窗口,'className':'chevron'})
        标样式模块(箭,样式模块)
        钮.appendChild(箭)
        def 切换(事件):
            '打开或关上行为菜单'
            自身.开=not 自身.开
            自身.渲染()
        钮.addEventListener('click',切换)
        def 选择(标识):
            '写入忙碌回车并关上'
            自身.开=False
            属性['setBusyEnter'](标识)
            自身.渲染()
        def 关上():
            '点外面就关'
            自身.开=False
            自身.渲染()
        单=菜单({
            'window':窗口,
            'open':自身.开,
            'items':[
                {'id':'queue','label':'排队发送'},
                {'id':'steer','label':'插话发送'},
            ],
            'selectedId':行为,
            'onSelect':选择,
            'onClose':关上,
            'align':'end',
            'anchor':钮,
        })
        行.appendChild(单.渲染())
        自身.根=行
        if 父 is not None:
            父.appendChild(自身.根)
        if not 自身.已订:
            钩=属性.get('useBusyEnter')
            if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                def 变更():
                    '偏好变了就重画'
                    if 自身.根 is not None and 自身.根.parentNode is not None:
                        自身.渲染()
                钩._subscribe(变更)
            自身.已订=True
        return 自身.根
