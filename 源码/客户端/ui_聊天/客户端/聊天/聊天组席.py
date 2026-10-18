import time as 时间模块
from ....ui_基础界面组件.icons import 图标,图标上chevron14,图标下箭头描边常规
from ....ui_基础界面组件.文字闪烁 import 文字闪烁
from ....ui_对话.异常 import 标样式模块
from ..存储 import 回合过程是否打开
from .步骤过程 import 过程标题
from .流程动效 import 正在隐藏或收起
from .用披露 import 注入聊天样式,取钩,真属性,挂节点
from .用过程滚动 import 过程滚动
from .渲染条目 import 聊天渲染键
from .聊天节点席 import 聊天节点席

__all__=['聊天组席']

样式模块='chat-group'
标题最短毫秒=150
活动图标={
    'thinking':'think-14',
    'read':'browse-16',
    'readImage':'browse-16',
    'search':'search-16',
    'edit':'edit-16',
    'write':'edit-16',
    'commands':'api-14',
    'code':'code-16',
    'webSearch':'globe-14',
    'webFetch':'browse-16',
    'subagents':'agent-preset-16',
    'plan':'checklist-14',
    'questions':'question-14',
    'tools':'sparkle-16',
}


def 同一标题(左,右):
    '活动、细节和是否准备中都一样'
    return 左.get('activity')==右.get('activity') and 左.get('detail')==右.get('detail') and 左.get('preparing')==右.get('preparing')


class 聊天组席:
    '过程组。显示策略只改可见性，不改成员的父节点'
    def __init__(自身,属性=None):
        '记下组键'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.头盒=None
        自身.体盒=None
        自身.内容盒=None
        自身.打开=False
        自身.滚动=过程滚动()
        自身.显示标题=None
        自身.显示于=0
        自身.定时=None
        自身.席表={}
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 稳定标题(自身,想要,活动):
        '活动标题至少停 150 毫秒，避免闪'
        if not 活动:
            自身.显示标题=想要
            return 想要
        if 自身.显示标题 is None or 同一标题(自身.显示标题,想要):
            if 自身.显示标题 is None:
                自身.显示标题=想要
                自身.显示于=int(时间模块.time()*1000)
            return 自身.显示标题
        剩余=标题最短毫秒-(int(时间模块.time()*1000)-自身.显示于)
        if 剩余<=0:
            自身.显示标题=想要
            自身.显示于=int(时间模块.time()*1000)
            return 想要
        if 自身.定时 is None and 'window' in 自身.属性 and hasattr(自身.属性['window'],'setTimeout'):
            def 提交():
                '到点后换成最新标题'
                自身.定时=None
                自身.显示标题=想要
                自身.显示于=int(时间模块.time()*1000)
                自身.渲染()
            自身.定时=自身.属性['window'].setTimeout(提交,剩余)
        return 自身.显示标题

    def 渲染(自身):
        '成组时画头。成员始终留在内容里'
        属性=自身.属性
        if 'window' not in 属性:
            return 自身.根
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'聊天组席.module.css')
        组键=属性.get('groupKey')
        取组=属性.get('useChatGroup')
        成员=None
        数据=None
        if callable(取组):
            def 选成员(组):
                '成员表'
                return None if not isinstance(组,dict) else 组.get('members')

            def 选数据(组):
                '组数据'
                return None if not isinstance(组,dict) else 组.get('data')

            成员=取组(组键,选成员)
            数据=取组(组键,选数据)
        if 成员 is None:
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            return None
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        策略=取钩(属性,'usePresentation')
        if 策略 is None:
            策略=属性.get('usePresentation')
        首键=成员[0].get('key') if len(成员)>0 and isinstance(成员[0],dict) else ''
        贴底=属性.get('useChatNodeBottom')
        在底=贴底(首键) is True if callable(贴底) else False
        推迟收=在底 and 属性.get('deferCollapse') is True
        过程=选过程(属性.get('useChatNodeProcess'),首键)
        节点钩=属性.get('useChatNode')
        回合位=None
        if callable(节点钩):
            def 选回合(节点):
                '节点所在回合'
                if not isinstance(节点,dict):
                    return None
                位置=节点.get('location')
                if isinstance(位置,dict) and 位置.get('kind') in ('turn','step'):
                    return 位置.get('turn')
                return None
            回合位=节点钩(首键,选回合)
        成组=False
        推迟完成=False
        if callable(策略):
            def 选成组(政策):
                '历史模式里，没结束且不推迟的回合保持平铺'
                if not isinstance(政策,dict):
                    return False
                if 政策.get('stepGrouping')=='collapsed':
                    return True
                开着=isinstance(回合位,dict) and 回合位.get('status')=='open'
                return 政策.get('stepGrouping')=='history' and not 开着 and not 推迟收

            def 选推迟(政策):
                '下一输入才折叠'
                return isinstance(政策,dict) and 政策.get('collapseTiming')=='next-input'

            def 选折完成(政策):
                '完成回合折叠'
                return isinstance(政策,dict) and 政策.get('foldCompletedTurns') is True

            成组=策略(选成组) is True
            推迟完成=策略(选推迟) is True
            折完成=策略(选折完成) is True
        else:
            折完成=False
        原因=None
        if isinstance(回合位,dict) and isinstance(回合位.get('end'),dict):
            尾数据=回合位['end'].get('data') if isinstance(回合位['end'].get('data'),dict) else {}
            原因体=尾数据.get('reason') if isinstance(尾数据.get('reason'),dict) else {}
            原因=原因体.get('kind')
        总开=isinstance(过程,dict) and (过程.get('turnClosed') is False or 过程.get('hasInterleavedInput') is True or 原因 in ('aborted','interrupted','error'))
        规格=过程.get('spec') if isinstance(过程,dict) else None
        已存开=False
        if isinstance(规格,dict) and callable(属性.get('useStore')):
            def 选开(状态):
                '存储里的开合'
                return 回合过程是否打开(状态,规格,推迟收)
            已存开=属性['useStore'](选开) is True
        外隐=折完成 and isinstance(过程,dict) and 过程.get('turnClosed') is True and isinstance(规格,dict) and not 总开 and not 已存开

        def 揭外():
            '展开外层回合过程'
            if isinstance(规格,dict) and not 总开 and isinstance(属性.get('actions'),dict) and callable(属性['actions'].get('setTurnProcessOpen')):
                属性['actions']['setTurnProcessOpen'](规格.get('turn'),规格.get('answerStep') or 0,True)

        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='root'
            标样式模块(自身.根,样式模块)
        组动作=取钩(属性,'useGroupAction')
        if 组动作 is None:
            组动作=属性.get('useGroupAction')
        if callable(组动作):
            if getattr(自身,'外席',None) is None:
                自身.外席=组动作(外隐,揭外)
            elif hasattr(自身.外席,'准备'):
                自身.外席.准备(外隐,揭外)
            if hasattr(自身.外席,'绑'):
                自身.外席.绑(自身.根)
        if 外隐 and 自身.根 is not None and 正在隐藏或收起(自身.根):
            自身.打开=False
        自身.根.setAttribute('data-chat-group-key','' if 组键 is None else str(组键))
        自身.根.setAttribute('data-chat-flow-key','' if 组键 is None else str(组键))
        自身.根.setAttribute('data-chat-anchor-key','group:'+str(组键))
        if isinstance(数据,dict) and 数据.get('turn') is not None:
            自身.根.setAttribute('data-chat-turn',str(数据.get('turn')))
        真属性(自身.根,'data-chat-paging-anchor',成组 and not 自身.打开)
        自身.根.setAttribute('data-step-process','')
        真属性(自身.根,'data-group-expanded-mode',not 成组)
        if 自身.头盒 is None:
            自身.头盒=文档.createElement('div')
            自身.根.appendChild(自身.头盒)
        头动作=属性.get('useGroupHeaderAction')
        if callable(头动作):
            class 引用:
                '给组头动效一个 current'
            if not hasattr(自身,'头引用'):
                自身.头引用=引用()
            自身.头引用.current=自身.头盒
            头动作(自身.头引用,not 成组 or (推迟完成 and 外隐))
        while 自身.头盒.firstChild is not None:
            自身.头盒.removeChild(自身.头盒.firstChild)
        if isinstance(数据,dict):
            自身.头盒.appendChild(自身.画头(文档,窗口,数据,翻译,策略))
        if 自身.体盒 is None:
            自身.体盒=文档.createElement('div')
            自身.根.appendChild(自身.体盒)
        体号='group-body-'+str(id(自身))
        自身.体盒.id=体号
        封顶=成组 and (not 推迟完成 or 自身.打开)
        类名='body'
        if not 封顶:
            类名=类名+' expandedBody'
        if 封顶 and 自身.滚动.边.get('canScrollUp'):
            类名=类名+' fadeTop'
        if 封顶 and 自身.滚动.边.get('canScrollDown'):
            类名=类名+' fadeBottom'
        自身.体盒.className=类名
        标样式模块(自身.体盒,样式模块)
        自身.体盒.setAttribute('data-step-process-body','')
        真属性(自身.体盒,'data-scroll-up',自身.滚动.边.get('canScrollUp') is True)
        真属性(自身.体盒,'data-scroll-down',自身.滚动.边.get('canScrollDown') is True)
        if 自身.内容盒 is None:
            自身.内容盒=文档.createElement('div')
            自身.内容盒.className='content'
            标样式模块(自身.内容盒,样式模块)
            自身.内容盒.setAttribute('data-step-process-content','')
            自身.内容盒.setAttribute('data-chat-flow','')
            自身.体盒.appendChild(自身.内容盒)
        仍在=set()
        for 员 in 成员:
            if not isinstance(员,dict):
                continue
            员键=聊天渲染键(员)
            仍在.add(员键)
            席属性=dict(属性)
            席属性.pop('parent',None)
            席属性['nodeKey']=员.get('key')
            if 员.get('groupPart') is not None:
                席属性['groupPart']=员.get('groupPart')
            if 员键 not in 自身.席表:
                席属性['parent']=自身.内容盒
                自身.席表[员键]=聊天节点席(席属性)
            else:
                自身.席表[员键].更新(席属性)
                自身.席表[员键].渲染()
        for 旧键 in list(自身.席表):
            if 旧键 not in 仍在:
                旧=自身.席表.pop(旧键)
                if 旧.根 is not None:
                    旧.根.remove()
        自身.滚动.挂(自身.体盒,自身.内容盒,自身.打开,成组)
        if not getattr(自身,'已听滚动',False):
            自身.已听滚动=True
            自身.体盒.addEventListener('scroll',自身.滚动.滚动)
            自身.体盒.addEventListener('wheel',自身.滚动.滚轮)
            自身.体盒.addEventListener('touchstart',自身.滚动.按下)
            自身.体盒.addEventListener('pointerdown',自身.滚动.按下)
            自身.体盒.addEventListener('keydown',自身.滚动.按键)

        def 揭内():
            '打开本地披露'
            自身.打开=True

        if callable(组动作):
            if getattr(自身,'内席',None) is None:
                自身.内席=组动作(成组 and not 自身.打开,揭内)
            elif hasattr(自身.内席,'准备'):
                自身.内席.准备(成组 and not 自身.打开,揭内)
            if hasattr(自身.内席,'绑'):
                自身.内席.绑(自身.体盒)
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        return 自身.根

    def 画头(自身,文档,窗口,数据,翻译,策略):
        '闭合用计数标题。进行中用稳定的活动标题'
        摘要=数据.get('summary') if isinstance(数据.get('summary'),dict) else {}
        想要={
            'activity':摘要.get('running') or 'thinking',
            'detail':摘要.get('runningDetail') or '',
            'preparing':摘要.get('preparing') is True,
        }
        活=自身.稳定标题(想要,数据.get('closed') is not True)
        if 数据.get('closed') is True:
            标签=过程标题(摘要,翻译)
            细节=''
            计数=摘要.get('counts') if isinstance(摘要.get('counts'),list) else []
            活动=计数[0].get('kind') if len(计数)>0 and isinstance(计数[0],dict) else 'thinking'
        else:
            if 活.get('preparing'):
                活动名='tools' if 活.get('activity')=='thinking' else 活.get('activity')
                标签=翻译('message.stepProcess.prepare.'+str(活动名))
            else:
                标签=翻译('message.stepProcess.'+str(活.get('activity')))
            详细=False
            if callable(策略) and 数据.get('closed') is False:
                def 选细(政策):
                    '进行中且策略要明细'
                    return isinstance(政策,dict) and 政策.get('liveProcessDetail') is True
                详细=策略(选细) is True
            细节=活.get('detail') or '' if 详细 else ''
            活动=活.get('activity')
        标题=标签 if 细节=='' else 标签+翻译('message.turnProcess.separator')+细节
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='title'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
        钮.setAttribute('aria-controls',自身.体盒.id if 自身.体盒 is not None else '')
        钮.setAttribute('data-process-activity',str(活动))

        def 切换(事件=None):
            '打开时按闭合与否定到顶或底'
            if hasattr(钮,'focus'):
                钮.focus()
            if not 自身.打开:
                自身.滚动.初始化('bottom' if 数据.get('closed') is False else 'top')
            自身.打开=not 自身.打开
            自身.渲染()

        钮.addEventListener('click',切换)
        前=文档.createElement('span')
        前.className='leading'
        标样式模块(前,样式模块)
        前.setAttribute('aria-hidden','true')
        图盒=文档.createElement('span')
        图盒.className='activityIcon'
        标样式模块(图盒,样式模块)
        图盒.setAttribute('data-step-process-icon','')
        图=图标(活动图标.get(活动,'sparkle-16'),{'window':窗口})
        if 图 is not None:
            图盒.appendChild(图)
        折盒=文档.createElement('span')
        折盒.className='chevron'
        标样式模块(折盒,样式模块)
        折盒.setAttribute('data-step-process-chevron','')
        折=图标上chevron14({'window':窗口}) if 自身.打开 else 图标下箭头描边常规({'window':窗口})
        if 折 is not None:
            折盒.appendChild(折)
        前.appendChild(图盒)
        前.appendChild(折盒)
        钮.appendChild(前)
        闪=文字闪烁({'window':窗口,'active':数据.get('closed') is not True,'children':标题,'className':'label'})
        挂节点(钮,闪)
        return 钮


def 选过程(钩,键):
    '过程呈现'
    if not callable(钩):
        return None
    return 钩(键)
