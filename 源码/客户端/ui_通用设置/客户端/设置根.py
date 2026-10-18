import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import (
    图标个性化16,
    图标归档20,
    图标刷新14,
    图标数据16,
    图标用户16,
    图标智能体预设16,
    图标设置16,
    图标勾描边常规,
    图标关闭描边常规,
)
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.模态层 import 使用模态层
from ...ui_基础界面组件.状态点 import 处理状态点
from .文案 import 中文
from .桌面更新指示器 import 桌面更新指示

__all__=['设置根']

样式模块='settingsRoot'
恢复确认毫秒=2000
连接中最少可见毫秒=800

def 现在毫秒(窗口):
    '浏览器 Date.now'
    return 窗口.Date.now()

def 注入设置样式(文档):
    '设置壳样式只插一次'
    注入模块样式文件(
        文档,
        '设置根样式',
        os.path.join(os.path.dirname(__file__),'设置根.module.css'),
        样式模块,
    )

class 连接指示:
    '断开、连接中、已恢复三态。共享连接指示器还不在基础界面里，这里按那三态画字和点击'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '没有状态就不占位。连接中是带点的按钮，已恢复是状态条'
        属性=自身.属性
        状态=属性['state']
        if 状态 is None:
            自身.根=None
            return None
        窗口=属性['window']
        文档=窗口.document
        if 状态=='recovered':
            条=文档.createElement('div')
            条.setAttribute('role','status')
            条.setAttribute('aria-label',属性['recoveredLabel'])
            图标盒=文档.createElement('span')
            图标盒.setAttribute('aria-hidden','true')
            图标盒.appendChild(图标勾描边常规({'window':窗口,'size':14}))
            条.appendChild(图标盒)
            字=文档.createElement('span')
            字.textContent=属性['recoveredLabel']
            条.appendChild(字)
            自身.根=条
            return 条
        连接中=状态=='connecting'
        钮=文档.createElement('button')
        钮.type='button'
        钮.setAttribute('data-phase',状态)
        if 连接中:
            钮.setAttribute('aria-label',属性['restartActionLabel'])
        else:
            钮.setAttribute('aria-label',属性['reconnectActionLabel'])
        图标盒=文档.createElement('span')
        图标盒.setAttribute('aria-hidden','true')
        if 连接中:
            图标盒.appendChild(处理状态点(窗口,{'state':'ongoing','size':14}))
        else:
            图标盒.appendChild(图标刷新14({'window':窗口,'size':14}))
        钮.appendChild(图标盒)
        字=文档.createElement('span')
        if 连接中:
            字.appendChild(文档.createTextNode(属性['connectingLabel']))
            点串=文档.createElement('span')
            点串.setAttribute('aria-hidden','true')
            for 点字 in ('.','.','.'):
                一点=文档.createElement('span')
                一点.textContent=点字
                点串.appendChild(一点)
            字.appendChild(点串)
        else:
            字.textContent=属性['disconnectedLabel']
        钮.appendChild(字)
        def 点(事件):
            '请求立刻重连'
            属性['onReconnect']()
        钮.addEventListener('click',点)
        自身.根=钮
        return 钮

class 设置面板:
    '盖住视口的设置对话框。遮罩、关闭钮和 Escape 都关'
    def __init__(自身,属性):
        '记下份额并画出'
        自身.属性=属性
        自身.根=None
        自身.对话框=None
        自身.标题标识='settings-title-'+str(id(自身))
        自身.渲染()

    def 渲染(自身):
        '请求的分区不在了就落到第一行'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入设置样式(文档)
        行表=属性['rows']
        活动=None
        for 行 in 行表:
            if 行['id']==属性['activeId']:
                活动=行['id']
                break
        if 活动 is None and len(行表)>0:
            活动=行表[0]['id']
        罩=模块节点(文档,'div',样式模块,'overlay')
        罩.setAttribute('role','presentation')
        遮罩=模块节点(文档,'div',样式模块,'mask')
        遮罩.setAttribute('aria-hidden','true')
        def 点遮罩(事件):
            '点遮罩关闭'
            属性['onClose']()
        遮罩.addEventListener('click',点遮罩)
        罩.appendChild(遮罩)
        面板=模块节点(文档,'div',样式模块,'panel')
        面板.setAttribute('tabindex','-1')
        面板.setAttribute('data-shortcut-modal','settings')
        面板.setAttribute('role','dialog')
        面板.setAttribute('aria-modal','true')
        面板.setAttribute('aria-labelledby',自身.标题标识)
        导航=模块节点(文档,'nav',样式模块,'nav')
        题=模块节点(文档,'div',样式模块,'navTitle')
        题.id=自身.标题标识
        题.setAttribute('tabindex','-1')
        if 活动 is None:
            题.setAttribute('data-modal-autofocus','')
        题.appendChild(属性['renderSlot']('settings.header',{'window':窗口}))
        导航.appendChild(题)
        列表=模块节点(文档,'div',样式模块,'navList')
        def 点节(标识):
            '选中这一节'
            def 点(事件):
                '交给壳存储'
                属性['onSelect'](标识)
            return 点
        for 行 in 行表:
            类名='navCell'
            if 行['id']==活动:
                类名='navCell active'
            钮=模块节点(文档,'button',样式模块,类名)
            钮.type='button'
            if 行['id']==活动:
                钮.setAttribute('aria-current','true')
                钮.setAttribute('data-modal-autofocus','')
            钮.addEventListener('click',点节(行['id']))
            标识=行['id']
            if 标识=='account':
                图=图标用户16({'window':窗口,'size':16,'className':'navIcon'})
            elif 标识=='models':
                图=图标数据16({'window':窗口,'size':16,'className':'navIcon'})
            elif 标识=='agent-presets':
                图=图标智能体预设16({'window':窗口,'size':16,'className':'navIcon'})
            elif 标识=='plugins':
                图=图标个性化16({'window':窗口,'size':16,'className':'navIcon'})
            elif 标识=='archived-sessions':
                图=图标归档20({'window':窗口,'size':16,'className':'navIcon'})
            else:
                图=图标设置16({'window':窗口,'size':16,'className':'navIcon'})
            标样式模块(图,样式模块)
            钮.appendChild(图)
            名=模块节点(文档,'span',样式模块,'navLabel')
            名.textContent=行['label']
            钮.appendChild(名)
            列表.appendChild(钮)
        导航.appendChild(列表)
        面板.appendChild(导航)
        内容=模块节点(文档,'div',样式模块,'content')
        头=模块节点(文档,'div',样式模块,'header')
        动作区=模块节点(文档,'div',样式模块,'actions')
        动作区.appendChild(属性['renderSlot']('settings.action',{'window':窗口}))
        头.appendChild(动作区)
        关=模块节点(文档,'button',样式模块,'close')
        关.type='button'
        def 点关(事件):
            '点关闭'
            属性['onClose']()
        关.addEventListener('click',点关)
        关.appendChild(图标关闭描边常规({'window':窗口,'size':14}))
        隐=模块节点(文档,'span',样式模块,'hiddenLabel')
        隐.appendChild(属性['renderSlot']('settings.close',{'window':窗口}))
        关.appendChild(隐)
        头.appendChild(关)
        内容.appendChild(头)
        选项=模块节点(文档,'div',样式模块,'options')
        if 活动 is not None:
            选项.appendChild(属性['renderSlot'](
                'settings.section',
                {'close':属性['onClose'],'window':窗口},
                {'only':活动},
            ))
        内容.appendChild(选项)
        面板.appendChild(内容)
        罩.appendChild(面板)
        自身.根=罩
        自身.对话框=面板
        return 罩

class 设置根:
    '侧栏底部的设置触发器、设置对话框和引导'
    def __init__(自身,属性):
        '记下份额、本地查看状态，并画出'
        自身.属性=属性
        自身.根=None
        自身.请求引导=None
        自身.已完成引导=set()
        自身.显示恢复=False
        自身.保持连接中=False
        自身.连接中显示于=None
        自身.上次连接=None
        自身.连接已记=False
        自身.见过引导=None
        自身.引导初见=False
        自身.恢复定时=None
        自身.保持定时=None
        自身.罩=None
        自身.卸模态=None
        自身.触发提示=None
        自身.指示=None
        自身.触发签名=None
        自身.面板签名=None
        自身.引导签名=None
        自身.行=None
        自身.指示位=None
        自身.引导位=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换份额'
        自身.属性=属性

    def 打开引导(自身,标识):
        '先关掉设置，再点名这一步引导'
        自身.属性['actions']['close']()
        自身.请求引导=标识
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 完成引导(自身,标识):
        '这一步结束。显式请求清掉，已完成的不重复记'
        自身.请求引导=None
        if 标识 not in 自身.已完成引导:
            下一=set(自身.已完成引导)
            下一.add(标识)
            自身.已完成引导=下一
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 卸罩(自身):
        '卸掉模态层和传送到 body 的面板'
        if 自身.卸模态 is not None:
            自身.卸模态()
            自身.卸模态=None
        if 自身.罩 is not None and 自身.罩.parentNode is not None:
            自身.罩.remove()
        自身.罩=None

    def 停定时(自身):
        '停掉恢复确认和连接中最短显示'
        窗口=自身.属性['window']
        if 自身.恢复定时 is not None:
            窗口.clearTimeout(自身.恢复定时)
            自身.恢复定时=None
        if 自身.保持定时 is not None:
            窗口.clearTimeout(自身.保持定时)
            自身.保持定时=None

    def 拆订阅(自身):
        '退掉壳上的钩子'
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False

    def 拆除(自身):
        '退订、停定时、卸面板和提示泡'
        自身.拆订阅()
        自身.停定时()
        自身.卸罩()
        if 自身.触发提示 is not None and callable(自身.触发提示.卸):
            自身.触发提示.卸()
        自身.触发提示=None
        if 自身.指示 is not None:
            自身.指示.拆除()
            自身.指示=None

    def 渲染(自身):
        '触发器、可选对话框、可选引导。连接中至少停 800 毫秒，恢复确认停 2 秒'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            注入设置样式(文档)
            def 全表(值):
                '整份快照'
                return 值
            def 找打开(行表):
                '打开设置这条命令'
                for 行 in 行表:
                    if 行['id']=='settings.open':
                        return 行
                return None
            def 选引导(状态):
                'ready 且主视图会话空白或没有主视图会话'
                主=None
                for 会话 in 状态['byId'].values():
                    保留=会话['retainedBy']
                    if 'mainView' in 保留 and 保留['mainView'] is not None:
                        次数=保留['mainView']
                    else:
                        次数=0
                    if 次数>0:
                        主=会话
                        break
                空白=主 is None or 主.get('blank') is True
                return 状态['phase']=='ready' and 空白
            壳状态=属性['useStore'](全表)
            打开=壳状态['open'] is True
            活动标识=壳状态['activeId']
            动作=属性['actions']
            宽=属性['wide'] is True
            快捷=属性['useShortcuts'](找打开)
            行表=属性['useSections'](全表)
            桌面视图=属性['useDesktopUpdate'](全表)
            连接=属性['useConnectionState'](全表)
            引导步骤=属性['useOnboardingSteps'](全表)
            引导活跃=属性['useSessions'](选引导)
            if 引导活跃 is False and len(自身.已完成引导)>0:
                自身.已完成引导=set()
            if 自身.请求引导 is not None:
                步骤=None
                for 步 in 引导步骤:
                    if 步['id']==自身.请求引导:
                        步骤=步
                        break
            elif 引导活跃:
                步骤=None
                for 步 in 引导步骤:
                    if 步['id'] not in 自身.已完成引导:
                        步骤=步
                        break
            else:
                步骤=None
            if 自身.引导初见 is False:
                自身.见过引导=步骤
                自身.引导初见=True
            else:
                出现=自身.见过引导 is None and 步骤 is not None
                自身.见过引导=步骤
                if 出现 and 打开:
                    动作['close']()
                    打开=False
            if 自身.连接已记 is False or 连接!=自身.上次连接:
                先前=连接 if 自身.连接已记 is False else 自身.上次连接
                自身.上次连接=连接
                自身.连接已记=True
                if 连接!='connected':
                    自身.显示恢复=False
                elif 先前=='disconnected' or 先前=='connecting':
                    自身.显示恢复=True
                if 自身.保持定时 is not None:
                    窗口.clearTimeout(自身.保持定时)
                    自身.保持定时=None
                if 连接=='connecting':
                    自身.保持连接中=False
                    自身.连接中显示于=现在毫秒(窗口)
                else:
                    显示于=自身.连接中显示于
                    if 显示于 is not None:
                        自身.连接中显示于=None
                        剩余=连接中最少可见毫秒-(现在毫秒(窗口)-显示于)
                        if 剩余>0:
                            自身.保持连接中=True
                            def 放开():
                                '最短显示结束'
                                自身.保持定时=None
                                自身.保持连接中=False
                                if 自身.绘制中:
                                    自身.待重画=True
                                    return
                                自身.渲染()
                            自身.保持定时=窗口.setTimeout(放开,剩余)
                        else:
                            自身.保持连接中=False
                    else:
                        自身.保持连接中=False
            if 自身.显示恢复 and 自身.保持连接中 is False:
                if 自身.恢复定时 is None:
                    def 收起():
                        '两秒后收起已连接'
                        自身.恢复定时=None
                        自身.显示恢复=False
                        if 自身.绘制中:
                            自身.待重画=True
                            return
                        自身.渲染()
                    自身.恢复定时=窗口.setTimeout(收起,恢复确认毫秒)
            elif 自身.恢复定时 is not None:
                窗口.clearTimeout(自身.恢复定时)
                自身.恢复定时=None
            指示状态=None
            if 连接=='connecting' or 自身.保持连接中:
                指示状态='connecting'
            elif 连接=='disconnected':
                指示状态='disconnected'
            elif 自身.显示恢复:
                指示状态='recovered'
            呈现=桌面视图.get('presentation')
            阶段=None if 呈现 is None else 呈现.get('phase')
            传给指示=None
            if 宽 and 阶段!='installing':
                传给指示=指示状态
            隐藏更新=指示状态 is not None and 阶段!='installing'
            if 自身.根 is None:
                自身.根=文档.createElement('div')
                自身.根.style.display='contents'
                自身.行=文档.createElement('div')
                自身.指示位=文档.createElement('div')
                自身.指示位.style.display='contents'
                自身.引导位=文档.createElement('div')
                自身.引导位.style.display='contents'
                自身.行.appendChild(自身.指示位)
                自身.根.appendChild(自身.行)
                自身.根.appendChild(自身.引导位)
            行类='triggerRow'
            if 宽 is False:
                行类='triggerRow railRow'
            自身.行.className=行类
            标样式模块(自身.行,样式模块)
            快捷键=None
            if 快捷 is not None and isinstance(快捷.get('keys'),list):
                快捷键=tuple(快捷['keys'])
            快捷读法=None if 快捷 is None else 快捷.get('aria')
            触发签名=(宽,打开,快捷键,快捷读法)
            if 自身.触发签名!=触发签名:
                if 自身.触发提示 is not None and callable(自身.触发提示.卸):
                    自身.触发提示.卸()
                自身.触发提示=None
                子=自身.行.firstChild
                while 子 is not None:
                    下=子.nextSibling
                    if 子 is not 自身.指示位:
                        子.remove()
                    子=下
                钮类='trigger'
                if 宽 is False:
                    钮类='trigger rail'
                钮=模块节点(文档,'button',样式模块,钮类)
                钮.type='button'
                钮.setAttribute('aria-label',中文['trigger'])
                钮.setAttribute('aria-haspopup','dialog')
                钮.setAttribute('aria-expanded','true' if 打开 else 'false')
                if 快捷读法 is not None:
                    钮.setAttribute('aria-keyshortcuts',快捷读法)
                def 点开(事件):
                    '打开设置'
                    动作['open']()
                钮.addEventListener('click',点开)
                钮.appendChild(属性['renderSlot']('settings.trigger',{'wide':宽,'window':窗口}))
                提示属性={
                    'window':窗口,
                    'label':中文['trigger'],
                    'disabled':打开,
                    'children':钮,
                }
                if 快捷键 is not None and len(快捷键)>0:
                    提示属性['shortcutKeys']=list(快捷键)
                自身.触发提示=提示泡(提示属性)
                启动拥有={
                    'wide':宽,
                    'settingsOpen':打开,
                    'openSettings':动作['open'],
                    'openOnboarding':自身.打开引导,
                    'window':窗口,
                }
                if 快捷键 is not None and len(快捷键)>0:
                    启动拥有['settingsShortcut']={'keys':list(快捷键),'aria':快捷读法}
                自身.行.insertBefore(属性['renderSlot'](
                    'settings.launcher',
                    启动拥有,
                    {'fallback':自身.触发提示.渲染()},
                ),自身.指示位)
                自身.触发签名=触发签名
            if 自身.指示 is not None:
                自身.指示.拆除()
                自身.指示=None
            while 自身.指示位.firstChild is not None:
                自身.指示位.firstChild.remove()
            指示=连接指示({
                'window':窗口,
                'state':传给指示,
                'disconnectedLabel':中文['connection.error'],
                'connectingLabel':中文['connection.connecting'],
                'recoveredLabel':中文['connection.connected'],
                'reconnectActionLabel':中文['connection.reconnect'],
                'restartActionLabel':中文['connection.restart'],
                'onReconnect':属性['reconnect'],
            })
            if 指示.根 is not None:
                自身.指示位.appendChild(指示.根)
            自身.指示=桌面更新指示({
                'window':窗口,
                'wide':宽,
                'hidden':隐藏更新,
                'view':桌面视图,
                'onOpen':属性['openDesktopUpdate'],
            })
            if 自身.指示.根 is not None:
                自身.指示位.appendChild(自身.指示.根)
            行元组=[]
            for 导航行 in 行表:
                行元组.append((导航行['id'],导航行['order'],导航行['label']))
            面板签名=(活动标识,tuple(行元组))
            if 打开 is False:
                自身.卸罩()
                自身.面板签名=None
            elif 自身.罩 is None or 自身.面板签名!=面板签名:
                自身.卸罩()
                面板件=设置面板({
                    'window':窗口,
                    'rows':行表,
                    'renderSlot':属性['renderSlot'],
                    'activeId':活动标识,
                    'onSelect':动作['select'],
                    'onClose':动作['close'],
                })
                罩=面板件.渲染()
                文档.body.appendChild(罩)
                自身.罩=罩
                自身.卸模态=使用模态层(面板件.对话框,True,动作['close'])
                自身.面板签名=面板签名
            if 步骤 is None:
                引导签名=None
            else:
                引导签名=(步骤['id'],自身.请求引导 is not None)
            if 自身.引导签名!=引导签名:
                while 自身.引导位.firstChild is not None:
                    自身.引导位.firstChild.remove()
                if 步骤 is not None:
                    自身.引导位.appendChild(属性['renderSlot']('settings.onboarding',{
                        'stepId':步骤['id'],
                        'explicit':自身.请求引导 is not None,
                        'complete':自身.完成引导,
                        'openSection':动作['openSection'],
                        'window':窗口,
                    },{'only':步骤['id']}))
                自身.引导签名=引导签名
            if 自身.已订 is False:
                自身.已订=True
                def 变更():
                    '壳上的快照变了就重画。根已经不在页面上就退订'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        自身.拆订阅()
                        return
                    自身.渲染()
                for 名 in (
                    'useStore',
                    'useShortcuts',
                    'useSections',
                    'useDesktopUpdate',
                    'useConnectionState',
                    'useOnboardingSteps',
                    'useSessions',
                ):
                    钩=属性.get(名)
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                        退=钩._subscribe(变更)
                        if callable(退):
                            自身.退订.append(退)
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
