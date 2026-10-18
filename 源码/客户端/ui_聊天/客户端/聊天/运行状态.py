import time as 时间模块
from ....ui_基础界面组件.文字闪烁 import 文字闪烁
from ....ui_对话.异常 import 标样式模块
from .消息铬 import 实况时钟间隔毫秒,格式化运行时长
from .用披露 import 注入聊天样式,挂节点

__all__=['运行状态']

样式模块='chat-view'
无障碍模块='a11y'
静止路径='M8.844 13.742C8.967 12.328 8.45 10.4 8.45 9.65C8.45 8.94 8.88 8.43 9.6 8.43C11.285 8.43 12.106 8.281 12.685 8.104C13.71 7.791 14.585 6.768 15.055 5.945C15.137 5.803 14.99 5.641 14.829 5.671C13.829 5.86 12.828 5.376 11.827 4.978C10.659 4.514 9.491 4.707 8.935 4.876C8.805 4.915 8.658 4.819 8.636 4.686C8.468 3.643 7.405 2.615 5.498 2.238C4.54 2.048 3.748 1.574 3.347 1.202C3.252 1.113 3.088 1.125 3.03 1.242C2.628 2.059 2.168 3.82 5.248 6.115C5.82 6.494 6.31 6.785 6.574 7.637C6.72 8.104 6.157 9.168 6.061 9.368C5.157 11.27 5.089 12.19 4.926 13.742'


class 运行状态:
    '回合还在跑时，流末尾的深度求索。有起点就按秒刷新用时'
    def __init__(自身,属性=None):
        '记下起始时间'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.定时=None
        自身.现在=int(时间模块.time()*1000)
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '静态鲸尾和闪烁文案。动画蒙版由样式决定，不另造图片'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'聊天视图.module.css')
        注入聊天样式(文档,无障碍模块,'无障碍.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            from ..文案 import 中文
            def 翻译(键,参数=None):
                '用包内中文表'
                文=中文.get(键,键)
                if isinstance(参数,dict):
                    for 名,值 in 参数.items():
                        文=文.replace('{'+名+'}',str(值))
                return 文
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='running'
            标样式模块(自身.根,样式模块)
            自身.根.setAttribute('data-chat-running','')
        else:
            while 自身.根.firstChild is not None:
                自身.根.removeChild(自身.根.firstChild)
        隐=文档.createElement('span')
        隐.className='visuallyHidden'
        标样式模块(隐,无障碍模块)
        隐.setAttribute('role','status')
        隐.setAttribute('aria-live','polite')
        隐.setAttribute('aria-atomic','true')
        隐.textContent=翻译('chat.deepDiving')
        自身.根.appendChild(隐)
        线=文档.createElement('span')
        线.className='runningDivider'
        标样式模块(线,样式模块)
        线.setAttribute('aria-hidden','true')
        自身.根.appendChild(线)
        内容=文档.createElement('span')
        内容.className='runningContent'
        标样式模块(内容,样式模块)
        图标=文档.createElement('span')
        图标.className='runningIcon'
        标样式模块(图标,样式模块)
        图标.setAttribute('aria-hidden','true')
        动画=文档.createElement('span')
        动画.className='runningWhaleAnimated'
        标样式模块(动画,样式模块)
        图标.appendChild(动画)
        静=文档.createElement('svg')
        静.className='runningWhaleStill'
        标样式模块(静,样式模块)
        静.setAttribute('width','100%')
        静.setAttribute('height','100%')
        静.setAttribute('viewBox','0 0 16 16')
        静.setAttribute('fill','none')
        路=文档.createElement('path')
        路.setAttribute('d',静止路径)
        路.setAttribute('stroke','currentColor')
        路.setAttribute('stroke-width','1')
        静.appendChild(路)
        图标.appendChild(静)
        内容.appendChild(图标)
        起点=属性.get('startTime')
        if 起点 is None:
            标签=翻译('chat.deepDiving')
        else:
            经过=max(1000,自身.现在-起点)
            时长=''.join(段.get('text') or '' for 段 in 格式化运行时长(经过,翻译))
            标签=翻译('chat.deepDivingFor',{'duration':时长})
        挂节点(内容,文字闪烁({'window':窗口,'active':True,'className':'runningText','children':标签}))
        自身.根.appendChild(内容)
        if 自身.定时 is not None and hasattr(窗口,'clearInterval'):
            窗口.clearInterval(自身.定时)
            自身.定时=None
        if 起点 is not None and hasattr(窗口,'setInterval'):
            def 走():
                '每秒刷新用时'
                自身.现在=int(时间模块.time()*1000)
                自身.渲染()
            自身.定时=窗口.setInterval(走,实况时钟间隔毫秒)
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        return 自身.根
