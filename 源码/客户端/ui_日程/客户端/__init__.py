from .文案 import 命名空间,中文,英文
from .管理文案 import 管理命名空间,管理中文,管理英文
from .目录源 import 创建目录源
from .删除提示 import 创建删除提示源,删除提示
from .定义 import 任务标识,任务种类,任务标签定义
from .任务标签绑定 import 任务标签绑定
from .会话链接 import 会话链接状态
from .会话日程状态 import 创建会话日程源
from .会话日程标记 import 会话日程标记
from .会话日程悬停 import 会话日程悬停
from .日程回合 import 日程回合定义
from .日程回合卡 import 日程回合卡
from .日程目录动作 import 日程目录动作
from .日程任务标签 import 日程任务标签
from .日程任务标签标题 import 日程任务标签标题
from .任务管理页 import 任务管理页
from .任务管理图标 import 任务管理图标

__all__=[
    '依赖','应用','命名空间','中文','英文',
    '会话日程标记','会话日程悬停',
]

依赖=['slots','locale']
面板标识='schedules'

def _服务(上下文,名):
    '未声明的服务用 get，避免属性代理把插件挂起'
    if hasattr(上下文,'get'):
        return 上下文.get(名)
    return getattr(上下文,名,None)

def 应用(上下文):
    '会话行标记、任务页、右栏任务、回合卡、页眉目录和删除提示。目录只读一次，不做重试循环。'
    def 登记词典():
        '行上词典和管理页词典一起登记'
        拆行=上下文.locale.register(命名空间,{'zh':中文,'en':英文})
        try:
            拆管理=上下文.locale.register(管理命名空间,{'zh':管理中文,'en':管理英文})
        except Exception:
            拆行()
            raise
        def 拆除():
            '两份词典一起卸'
            拆管理()
            拆行()
        return 拆除
    上下文.副作用(登记词典,'ui-schedule: dictionaries')

    def 远程日程():
        '宿主 schedule 远程面'
        远程=_服务(上下文,'remote')
        日程=getattr(远程,'schedule',None) if 远程 is not None else None
        if 日程 is None:
            raise RuntimeError('schedule catalog is unavailable')
        return 日程

    格子={'源':None}

    def 删除目录项(标识):
        '按目录里的会话标识删除。行上的标记不调用这里。'
        源=格子['源']
        快照=源['hooks']['catalog'].getSnapshot()
        记录列=快照['records'] if isinstance(快照,dict) and isinstance(快照.get('records'),list) else []
        记录=None
        for 项 in 记录列:
            if isinstance(项,dict) and 项.get('id')==标识:
                记录=项
                break
        if 记录 is None:
            return {'ok':True,'value':{'id':标识,'deleted':False,'code':'schedule_not_found'}}
        return 远程日程().delete({'sessionId':记录['sessionId'],'id':标识})

    def 订远端(事件,监听):
        'schedule/changed'
        远程=_服务(上下文,'remote')
        if 远程 is None:
            raise RuntimeError('schedule change subscription is unavailable')
        订=getattr(远程,'$on',None)
        if not callable(订):
            订=getattr(远程,'on',None)
        if not callable(订):
            raise RuntimeError('schedule change subscription is unavailable')
        return 订(事件,监听)

    目录=创建目录源({
        'list':lambda:远程日程().catalog(),
        'remove':删除目录项,
        'subscribeChanged':lambda 监听:订远端('schedule/changed',监听),
        'subscribeReset':lambda 监听:上下文.on('connection/reset',监听),
    })
    格子['源']=目录
    提示=创建删除提示源()

    def 报告删除(原删除):
        '删除落定后走同一条横幅'
        def 包装(标识):
            结局=原删除(标识)
            if hasattr(结局,'then') and callable(结局.then):
                return 结局.then(lambda 值:提示['report'](值) or 值)
            提示['report'](结局)
            return 结局
        return 包装

    def 更新任务(请求):
        '改名、说明或时刻。写入后按当时的读取序号再拉目录。'
        结果=远程日程().update(请求)
        def 再读(值):
            成功=isinstance(值,dict) and 值.get('ok') is True
            内容=值.get('value') if 成功 and isinstance(值.get('value'),dict) else {}
            if 成功 and ('record' in 内容 or 内容.get('code') in ('schedule_conflict','schedule_ended','schedule_not_found')):
                目录['onRetry'](目录['hooks']['catalog'].getSnapshot().get('readRequest'))
            return 值
        if hasattr(结果,'then') and callable(结果.then):
            return 结果.then(再读)
        return 再读(结果)

    def 读历史(请求):
        '投递历史'
        return 远程日程().history(请求)

    def 打开会话(标识):
        '会话仍在且未归档才打开'
        会话服务=_服务(上下文,'sessions')
        工作区=_服务(上下文,'workspaces')
        界面工作区=_服务(上下文,'uiWorkspace')
        if 会话服务 is None or 工作区 is None or 界面工作区 is None:
            raise RuntimeError('schedule session open is unavailable')
        if 会话链接状态(标识,会话服务.list.getSnapshot(),工作区.list.getSnapshot())!='available':
            return
        界面工作区.openSession(标识)

    def 活动标签(会话标识):
        '这一会话还开着的页'
        右栏=_服务(上下文,'sidebarRight')
        if 右栏 is None or not callable(getattr(右栏,'tabsIn',None)):
            return []
        return [页['id'] for 页 in 右栏.tabsIn(会话标识) if isinstance(页,dict) and 'id' in 页]

    绑定=任务标签绑定(活动标签)
    详情={
        'hooks':目录['hooks'],
        'onDelete':报告删除(目录['onDelete']),
        'onRetry':目录['onRetry'],
        'onUpdateTiming':更新任务,
        'loadHistory':读历史,
        'onOpenSession':打开会话,
    }

    def 登记提示():
        '删除结果留在壳上，面板关掉也还在'
        return 上下文.slots.register({
            'name':'shell.overlay',
            'id':'schedule.delete-toast',
            'locale':管理命名空间,
            'inject':lambda: {'hooks':提示['hooks'],'dismiss':提示['dismiss']},
        },删除提示)
    上下文.slots.inject('shell.overlay',登记提示)

    def 登记种类():
        '右栏任务页种类'
        右栏页=_服务(上下文,'sidebarRightTabs')
        if 右栏页 is None:
            raise RuntimeError('schedule task tab type is unavailable')
        翻译=上下文.locale.bind(管理命名空间)
        return 右栏页.register(任务标签定义(翻译))
    上下文.副作用(登记种类,'ui-schedule: task tab type')

    def 登记任务页():
        '右栏正文'
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab',
            'key':任务标识,
            'locale':管理命名空间,
            'inject':lambda: {**详情,'taskBindings':绑定},
        },日程任务标签)
    上下文.slots.inject('sidebar.right.pane.tab',登记任务页)

    def 登记任务标题():
        '右栏标题'
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab.title',
            'key':任务标识,
            'locale':管理命名空间,
            'inject':lambda: {'hooks':详情['hooks'],'taskBindings':绑定},
        },日程任务标签标题)
    上下文.slots.inject('sidebar.right.pane.tab.title',登记任务标题)

    def 登记任务管理():
        '主栏任务页。新建回到一条会话，页上没有创建表。'
        def 注入():
            def 新建():
                界面工作区=_服务(上下文,'uiWorkspace')
                if 界面工作区 is None or not callable(getattr(界面工作区,'startSession',None)):
                    raise RuntimeError('workspace start is unavailable')
                界面工作区.startSession()
            return {**详情,'onNewTask':新建}
        return 上下文.slots.register({
            'name':'main',
            'key':面板标识,
            'locale':管理命名空间,
            'inject':注入,
        },任务管理页)
    上下文.slots.inject('main',登记任务管理)

    def 登记面板():
        '侧栏面板入口'
        def 标签():
            return 上下文.locale.bind(管理命名空间)('panel')
        return 上下文.slots.register({
            'name':'sidebar.panellist',
            'id':面板标识,
            'order':10,
            'locale':管理命名空间,
            'label':标签,
        },任务管理图标)
    上下文.slots.inject('sidebar.panellist',登记面板)

    def 登记回合定义():
        '创建任务记在回合上'
        对话=_服务(上下文,'uiConversation')
        if 对话 is None or not hasattr(对话,'events'):
            raise RuntimeError('uiConversation is unavailable')
        return 对话.events.register(日程回合定义)
    上下文.副作用(登记回合定义,'ui-schedule: turn definition')

    def 登记回合卡():
        '回合尾的创建卡'
        def 注入(会话标识):
            def 打开详情(标识):
                右栏=_服务(上下文,'sidebarRight')
                if 右栏 is None or not callable(getattr(右栏,'openTab',None)):
                    raise RuntimeError('schedule task tab is unavailable')
                右栏.openTab(任务种类,{'params':{'sessionId':会话标识,'id':标识}})
            return {
                'hooks':{'catalog':目录['hooks']['catalog']},
                'onRetry':目录['onRetry'],
                'openTaskDetail':打开详情,
            }
        return 上下文.slots.register({
            'name':'conversation.chat.turnTail',
            'id':'schedule-created',
            'order':20,
            'locale':管理命名空间,
            'inject':注入,
        },日程回合卡)
    上下文.slots.inject('conversation.chat.turnTail',登记回合卡)

    def 登记页眉():
        '当前会话的活动提醒。只在页眉挂上时读取这一会话。'
        def 注入(会话标识):
            源=创建会话日程源(上下文,会话标识)
            def 打开详情(标识):
                右栏=_服务(上下文,'sidebarRight')
                if 右栏 is None or not callable(getattr(右栏,'openTab',None)):
                    raise RuntimeError('schedule task tab is unavailable')
                右栏.openTab(任务种类,{'params':{'sessionId':会话标识,'id':标识}})
            return {**源,'onDelete':报告删除(源['onDelete']),'openTaskDetail':打开详情}
        return 上下文.slots.register({
            'name':'conversation.session.header.utilities',
            'id':'schedule-catalog',
            'order':-5,
            'locale':命名空间,
            'inject':注入,
        },日程目录动作)
    上下文.slots.inject('conversation.session.header.utilities',登记页眉)

    def 注入目录():
        '可见行共用这一次目录读取'
        return {'hooks':{'catalog':目录['hooks']['catalog']}}

    def 登记标记():
        '会话行时钟'
        return 上下文.slots.register({
            'name':'sidebar.session.row.leading',
            'id':'schedule-mark',
            'order':10,
            'locale':命名空间,
            'inject':注入目录,
        },会话日程标记)
    上下文.slots.inject('sidebar.session.row.leading',登记标记)

    def 登记悬停():
        '悬停卡里的任务'
        return 上下文.slots.register({
            'name':'sidebar.session.row.hover',
            'id':'schedule-tasks',
            'order':10,
            'locale':命名空间,
            'inject':注入目录,
        },会话日程悬停)
    上下文.slots.inject('sidebar.session.row.hover',登记悬停)

inject=依赖
apply=应用
