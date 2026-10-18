import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,模块节点#样式模块
from ...ui_基础界面组件.icons import 描边图标,常规描边#右箭头
from ...ui_基础界面组件.文件类型图标 import 文件类型图标#Markdown 图标

__all__=['计划卡','计划审阅打开']

样式模块='plan-preview'


def 确保样式(文档):
    '计划卡和审阅链接共用预览样式'
    注入模块样式文件(
        文档,
        'dsh-plan-preview',
        os.path.join(os.path.dirname(__file__),'计划预览.module.css'),
        样式模块,
    )


def 订上(自身,名字列表):
    '钩子变了就重画。根被从页面拿掉就退订'
    if 自身.已订:
        return
    自身.已订=True
    def 变更():
        '重画，或在根离开页面后退订'
        if 自身.根 is not None and 自身.根.parentNode is None:
            for 退 in 自身.退订:
                退()
            自身.退订=[]
            自身.已订=False
            return
        自身.渲染()
    for 名 in 名字列表:
        钩=自身.属性.get(名)
        if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
            自身.退订.append(钩._subscribe(变更))


class 计划卡:
    '已完成回合里，按调用顺序排列的已提交计划'
    def __init__(自身,属性):
        '记下渲染器交来的 props，并画出卡片'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性

    def 渲染(自身):
        '没有计划就不占位置。有计划就逐张可点的卡'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            回合=属性['turn']
            计划列表=属性['usePlans'](str(回合['turn']))
            旧=自身.根
            父=旧.parentNode if 旧 is not None else 属性.get('parent')
            if 旧 is not None:
                旧.remove()
                自身.根=None
            if 计划列表 is None or len(计划列表)==0:
                自身.根=None
            else:
                盒=模块节点(文档,'div',样式模块,'cards')
                盒.setAttribute('data-plan-artifacts','true')
                for 一份 in 计划列表:
                    钮=模块节点(文档,'button',样式模块,'card')
                    钮.setAttribute('type','button')
                    钮.setAttribute('data-plan-card',一份['callId'])
                    钮.setAttribute('aria-label',f'打开计划：{一份["title"]}')

                    def 点开(事件,调用=一份['callId'],打开=属性['openPlan']):
                        '在侧栏打开这一份'
                        打开(调用)

                    钮.addEventListener('click',点开)
                    图标盒=模块节点(文档,'span',样式模块,'cardIcon')
                    图标盒.appendChild(文件类型图标({'window':窗口,'kind':'markdown','size':20}).渲染())
                    钮.appendChild(图标盒)
                    细节=模块节点(文档,'span',样式模块,'cardDetails')
                    标题=模块节点(文档,'span',样式模块,'cardTitle')
                    标题.textContent=一份['title']
                    说明=模块节点(文档,'span',样式模块,'cardDescription')
                    说明.textContent='计划 · Markdown'
                    细节.appendChild(标题)
                    细节.appendChild(说明)
                    钮.appendChild(细节)
                    动作=模块节点(文档,'span',样式模块,'cardOpen')
                    动作.textContent='打开'
                    钮.appendChild(动作)
                    盒.appendChild(钮)
                自身.根=盒
                if 父 is not None:
                    父.appendChild(盒)
            订上(自身,('usePlans',))
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根


class 计划审阅打开:
    '待审计划自动打开一次，并留下手动的查看全文'
    def __init__(自身,属性):
        '记下 props。还没有跑过自动打开'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.效应依赖=None
        自身.渲染()

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性

    def 渲染(自身):
        '侧栏挂上且还没自动打开过，就打开一次。按钮始终留着'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            审阅=属性['review']
            请求键=属性['requestKey']
            if 审阅.get('callId') is None:
                身份=f'review:{请求键}'
            else:
                身份=f'call:{审阅["callId"]}'

            def 已开选择(状态):
                '这个身份是否已经自动打开过'
                表=状态.get('opened') if isinstance(状态,dict) else None
                if isinstance(表,dict) is not True:
                    return False
                return 表.get(身份) is True

            def 在屏(会话):
                '有在屏会话才算侧栏挂上'
                return 会话 is not None

            已打开=属性['useStore'](已开选择)
            已挂载=属性['useSidebarMounted'](在屏)
            依赖=(身份,已打开,已挂载,请求键,id(审阅),id(属性.get('openReview')),id(属性.get('actions')))
            if 依赖!=自身.效应依赖:
                自身.效应依赖=依赖
                if 已打开 is not True and 已挂载 is True:
                    属性['openReview'](审阅,请求键)
                    属性['actions']['markOpened'](身份)
            旧=自身.根
            父=旧.parentNode if 旧 is not None else 属性.get('parent')
            if 旧 is not None:
                旧.remove()
                自身.根=None
            钮=模块节点(文档,'button',样式模块,'reviewLink')
            钮.setAttribute('type','button')
            钮.setAttribute('title','在侧边栏打开计划')
            钮.setAttribute('aria-label','在侧边栏打开计划')

            def 点开(事件,打开=属性['openReview'],这份=审阅,键=请求键):
                '再打开一次，不代替审批'
                打开(这份,键)

            钮.addEventListener('click',点开)
            钮.appendChild(文档.createTextNode('查看全文'))
            钮.appendChild(描边图标(
                {'window':窗口,'size':14},
                '0 0 16 16',
                ['M6 12L9.29289 8.70711C9.68342 8.31658 9.68342 7.68342 9.29289 7.29289L6 4'],
                14,
                常规描边,
            ))
            自身.根=钮
            if 父 is not None:
                父.appendChild(钮)
            订上(自身,('useStore','useSidebarMounted'))
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
