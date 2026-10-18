import os
import pywebbridge
from ...ui_基础界面组件.icons import 图标浅色16,图标深色16,图标跟随系统16
from ...ui_对话.异常 import 注入模块样式文件,模块节点
from .文案 import 中文

__all__=['外观行']

立方=(
    ('light','appearance.light',图标浅色16),
    ('dark','appearance.dark',图标深色16),
    ('system','appearance.system',图标跟随系统16),
)

class 外观行:
    '外观偏好：标题和浅色、深色、跟随系统三个方块'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性
        自身.根=None
        if isinstance(属性,dict) and 'window' in 属性 and 'setTheme' in 属性 and 'useStore' in 属性:
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
        注入模块样式文件(
            文档,
            '外观行样式',
            os.path.join(os.path.dirname(__file__),'外观行.module.css'),
            'appearance',
        )
        def 选偏好(快照):
            '持久偏好，不看已经解析的活动主题'
            return 快照['preference']
        偏好=属性['useStore'](选偏好)
        组=模块节点(文档,'div','appearance','group')
        标题=模块节点(文档,'div','appearance','title')
        标题.textContent=中文['appearance.title']
        组.appendChild(标题)
        排=模块节点(文档,'div','appearance','cubeRow')
        组.appendChild(排)
        for 标识,标签键,画图标 in 立方:
            类名='themeCube'
            if 偏好==标识:
                类名='themeCube selected'
            钮=模块节点(文档,'button','appearance',类名)
            钮.type='button'
            钮.setAttribute('aria-pressed','true' if 偏好==标识 else 'false')
            画图标({'window':窗口,'parent':钮})
            钮.appendChild(文档.createTextNode(中文[标签键]))
            def 点击(事件,选=标识):
                '写入该偏好'
                属性['setTheme'](选)
            钮.addEventListener('click',点击)
            排.appendChild(钮)
        if 'parent' in 属性:
            属性['parent'].appendChild(组)
        自身.根=组
        return 自身.根

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
