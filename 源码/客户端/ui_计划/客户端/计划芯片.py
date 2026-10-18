import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点#样式模块
from ...ui_基础界面组件.icons import 描边图标,常规描边#计划字形

__all__=['计划芯片']

样式模块='plan-chip'


class 计划芯片:
    '只在有效目标处于计划模式时出现。点击执行 /plan off'
    def __init__(自身,属性):
        '记下 props。还活着，还没在退出'
        自身.属性=属性
        自身.根=None
        自身.离开中=False
        自身.错误=None
        自身.存活=True
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性

    def 渲染(自身):
        '投影缺席或当前不是计划模式就不画。失败时旁边写退出失败'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入模块样式文件(
                文档,
                'dsh-plan-chip',
                os.path.join(os.path.dirname(__file__),'计划芯片.module.css'),
                样式模块,
            )
            计划值=属性['useProjection']('plan')
            旧=自身.根
            父=旧.parentNode if 旧 is not None else 属性.get('parent')
            if 旧 is not None:
                旧.remove()
                自身.根=None
            画出=False
            if 计划值 is not None:
                活动=bool(计划值.get('active'))
                if 计划值.get('pending'):
                    目标=not 活动
                else:
                    目标=活动
                画出=目标 is True
            if 画出 is not True:
                自身.根=None
            else:
                包裹=模块节点(文档,'span',样式模块,'wrap')
                钮=模块节点(文档,'button',样式模块,'chip')
                钮.setAttribute('type','button')
                钮.setAttribute('aria-label','计划模式已开启，按下关闭')
                钮.setAttribute('title','计划模式已开启 — 点击关闭（/plan off）')
                钮.disabled=bool(属性.get('locked')) or 自身.离开中

                def 关闭(事件):
                    '执行退出。离开中和锁定已经让按钮点不到'
                    自身.离开中=True
                    自身.错误=None
                    try:
                        失败=自身.属性['exitPlanMode']()
                    except Exception as 原因:
                        if 自身.存活 is not True:
                            return
                        自身.离开中=False
                        自身.错误=str(原因)
                    else:
                        if 自身.存活 is not True:
                            return
                        自身.离开中=False
                        自身.错误=失败
                    自身.渲染()

                钮.addEventListener('click',关闭)
                字形=模块节点(文档,'span',样式模块,'glyph')
                字形.setAttribute('aria-hidden','true')
                休息=描边图标(
                    {'window':窗口,'size':14,'className':'restGlyph'},
                    '0 0 16 16',
                    [
                        'M4.9375 5.90295H11.0625',
                        'M4.9375 9.02991H8.27841',
                        {'d':'M12.5 1.32617C13.3039 1.32617 14 1.95171 14 2.77637V7.61328L13 8.68164V2.77637C13 2.55186 12.8007 2.32617 12.5 2.32617H3.5C3.1993 2.32617 3 2.55186 3 2.77637V13.2246C3.00044 13.4489 3.19963 13.6738 3.5 13.6738H8.32812L7.39258 14.6738H3.5C2.69637 14.6738 2.00042 14.0489 2 13.2246V2.77637C2 1.95171 2.69613 1.32617 3.5 1.32617H12.5Z','fill':'currentColor'},
                        {'d':'M8.97212 14.3693C9.17511 14.5723 9.37811 14.7753 9.5811 14.9783C9.67012 14.8953 9.75914 14.8123 9.84815 14.7293C11.4505 13.2352 13.0528 11.7411 14.6551 10.247C14.7441 10.164 14.8331 10.081 14.9221 9.99803C14.5989 9.6748 14.2756 9.35157 13.9524 9.02834C13.8694 9.11736 13.7864 9.20637 13.7034 9.29539C12.2093 10.8977 10.7152 12.5 9.22113 14.1023C9.13813 14.1913 9.05513 14.2803 8.97212 14.3693Z','fill':'currentColor'},
                        {'d':'M11.6323 13.7841C11.6323 14.0395 11.6323 14.295 11.6323 14.5504C11.6812 14.5523 11.7301 14.5543 11.779 14.5562C12.659 14.5913 13.539 14.6263 14.419 14.6614C14.4679 14.6633 14.5168 14.6653 14.5657 14.6672C14.5657 14.3339 14.5657 14.0006 14.5657 13.6672C14.5168 13.6692 14.4679 13.6711 14.419 13.6731C13.539 13.7081 12.659 13.7432 11.779 13.7783C11.7301 13.7802 11.6812 13.7821 11.6323 13.7841Z','fill':'currentColor'},
                    ],
                    14,
                    常规描边,
                )
                字形.appendChild(标样式模块(休息,样式模块))
                悬停=文档.createElement('svg')
                悬停.setAttribute('width','14')
                悬停.setAttribute('height','14')
                悬停.setAttribute('viewBox','0 0 16 16')
                悬停.setAttribute('fill','none')
                悬停.setAttribute('xmlns','http://www.w3.org/2000/svg')
                悬停.setAttribute('aria-hidden','true')
                悬停.setAttribute('stroke-width',str(常规描边))
                悬停.setAttribute('class','hoverGlyph')
                路=文档.createElement('path')
                路.setAttribute('fill-rule','evenodd')
                路.setAttribute('clip-rule','evenodd')
                路.setAttribute('d','M15 8A7 7 0 1 1 1 8A7 7 0 1 1 15 8ZM6.409 10.652L5.348 9.591L6.939 8L5.348 6.409L6.409 5.348L8 6.939L9.591 5.348L10.652 6.409L9.061 8L10.652 9.591L9.591 10.652L8 9.061Z')
                路.setAttribute('fill','currentColor')
                悬停.appendChild(路)
                字形.appendChild(标样式模块(悬停,样式模块))
                钮.appendChild(字形)
                钮.appendChild(文档.createTextNode('计划'))
                包裹.appendChild(钮)
                if 自身.错误 is not None:
                    失败行=模块节点(文档,'span',样式模块,'error')
                    失败行.setAttribute('role','status')
                    失败行.setAttribute('title',str(自身.错误))
                    失败行.textContent='退出计划模式失败'
                    包裹.appendChild(失败行)
                自身.根=包裹
                if 父 is not None:
                    父.appendChild(包裹)
            if 自身.已订 is not True:
                自身.已订=True

                def 变更():
                    '投影变了就重画。根离开页面就标死并退订'
                    if 自身.根 is not None and 自身.根.parentNode is None:
                        自身.存活=False
                        for 退 in 自身.退订:
                            退()
                        自身.退订=[]
                        自身.已订=False
                        return
                    自身.渲染()

                钩=属性.get('useProjection')
                if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                    自身.退订.append(钩._subscribe(变更))
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
