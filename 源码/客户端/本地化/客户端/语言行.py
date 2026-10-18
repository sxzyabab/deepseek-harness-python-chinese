from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块
from ...ui_基础界面组件.icons import 图标下箭头描边常规
from ...ui_基础界面组件.菜单 import 菜单

__all__=['语言行']

样式模块='LanguageRow'
样式路径=os.path.join(os.path.dirname(__file__),'语言行.module.css')


class 语言行:
    '常规设置里的语言行。标题用中文表原文，菜单切换已登记语言'
    def __init__(自身,属性):
        '记下份额，菜单默认关闭，并画出这一行'
        自身.属性=属性
        自身.打开=False
        自身.根=None
        自身.按钮=None
        自身.菜单=None
        自身.退订=[]
        自身.已订=False
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 关闭(自身):
        '关掉菜单'
        自身.打开=False
        自身.渲染()

    def 选定(自身,标识):
        '先关菜单，再写入偏好'
        自身.打开=False
        自身.属性['setLocale'](标识)
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 切换(自身,事件=None):
        '点按钮开关菜单'
        自身.打开=not 自身.打开
        自身.渲染()

    def 拆除(自身):
        '退掉仓库订阅'
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False

    def 渲染(自身):
        '标题固定为语言。当前名称和选项来自语言行仓库'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性.get('window')
            if 窗口 is None:
                窗口=取握手窗口()
            文档=窗口.document
            注入模块样式文件(文档,'dsh-locale-language-row',样式路径,样式模块)
            def 选当前(状态):
                '当前语言 id'
                return 状态['active']
            def 选选项(状态):
                '可选语言'
                return 状态['options']
            当前=属性['useStore'](选当前)
            选项=属性['useStore'](选选项)
            标签=当前
            for 项 in 选项:
                if 项['id']==当前:
                    if 项.get('label') is not None:
                        标签=项['label']
                    break
            if 自身.根 is None:
                自身.根=模块节点(文档,'div',样式模块,'row')
                文区=模块节点(文档,'div',样式模块,'rowText')
                题=模块节点(文档,'div',样式模块,'title')
                题.textContent='语言'
                文区.appendChild(题)
                自身.根.appendChild(文区)
                自身.按钮=模块节点(文档,'button',样式模块,'selector')
                自身.按钮.setAttribute('type','button')
                自身.按钮.setAttribute('aria-haspopup','menu')
                自身.按钮.addEventListener('click',自身.切换)
            自身.按钮.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
            while 自身.按钮.firstChild is not None:
                自身.按钮.removeChild(自身.按钮.firstChild)
            自身.按钮.appendChild(文档.createTextNode(标签))
            图=图标下箭头描边常规({
                'window':窗口,
                'className':'chevron',
            })
            标样式模块(图,样式模块)
            自身.按钮.appendChild(图)
            菜单属性={
                'window':窗口,
                'open':自身.打开,
                'onClose':自身.关闭,
                'items':[{'id':项['id'],'label':项['label']} for 项 in 选项],
                'selectedId':当前,
                'onSelect':自身.选定,
                'align':'end',
                'portal':True,
                'anchor':自身.按钮,
                'parent':自身.根,
            }
            if 自身.菜单 is None:
                自身.菜单=菜单(菜单属性)
            else:
                自身.菜单.更新(菜单属性)
            自身.菜单.渲染()
            if 自身.已订 is False:
                自身.已订=True
                def 变更():
                    '仓库变了就重画。行已经不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        自身.拆除()
                        return
                    自身.渲染()
                退=属性['useStore']._subscribe(变更)
                if callable(退):
                    自身.退订.append(退)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
