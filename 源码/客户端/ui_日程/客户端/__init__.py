'浏览器里的任务页、页眉提醒、右栏详情、回合卡和会话行标记'
from . import (
    文案,
    管理文案,
    频率文案,
    定义,
    目录源,
    会话链接,
    会话日程状态,
    相对时钟,
    任务时刻,
    任务定时,
    日程格式,
    日程创建模型,
    日程回合,
    任务标签绑定,
    任务标签目标,
    日历图标,
    任务管理图标,
    目录反馈,
    删除提示,
    会话日程标记,
    会话日程悬停,
    日程创建卡,
    日程回合卡,
    日程任务标签,
    日程任务标签标题,
    日程目录动作,
    选择器弹出,
    日期选择,
    时钟选择,
    任务菜单,
    任务管理页,
    任务详情,
    投递历史,
)
from .文案 import 命名空间,目录中文,目录英文
from .管理文案 import 管理命名空间,管理中文,管理英文
from .定义 import 任务标识,任务种类
from .目录源 import 创建目录源
from .会话链接 import 会话链接状态
from .日程回合 import 日程回合定义
from .任务标签绑定 import 任务标签绑定
from .删除提示 import 删除提示
from .会话日程标记 import 会话日程标记
from .会话日程悬停 import 会话日程悬停
from .日程目录动作 import 日程目录动作
from .日程回合卡 import 日程回合卡
from .日程任务标签 import 日程任务标签
from .日程任务标签标题 import 日程任务标签标题
from .任务管理页 import 任务管理页
from .任务管理图标 import 任务管理图标

__all__=[
    '文案','管理文案','频率文案','定义','目录源','会话链接','会话日程状态','相对时钟',
    '任务时刻','任务定时','日程格式','日程创建模型','日程回合','任务标签绑定','任务标签目标',
    '日历图标','任务管理图标','目录反馈','删除提示','会话日程标记','会话日程悬停',
    '日程创建卡','日程回合卡','日程任务标签','日程任务标签标题','日程目录动作',
    '选择器弹出','日期选择','时钟选择','任务菜单','任务管理页','任务详情','投递历史',
    '依赖','应用',
]

依赖=[
    'slots','locale','remote','remote.schedule','conversation','uiConversation','uiWorkspace',
    'sessions','workspaces','sidebarRightTabs','sidebarRight',
]
面板标识='schedules'
inject=依赖


def 应用(上下文,配置=None):
    '登记词典、任务页、页眉目录、右栏详情、回合卡、行标记和删除横幅'
    def 登记目录词典():
        '活动提醒文案'
        return 上下文.locale.register(命名空间,{'zh':目录中文,'en':目录英文})

    def 登记管理词典():
        '任务页文案'
        return 上下文.locale.register(管理命名空间,{'zh':管理中文,'en':管理英文})

    上下文.effect(登记目录词典,'ui-schedule: dictionaries')
    上下文.effect(登记管理词典,'ui-schedule: manager dictionaries')

    提示状态={'state':None,'seq':0,'listeners':set()}

    def 发布提示(下一份):
        '通知壳上的横幅'
        提示状态['state']=下一份
        for 监听 in list(提示状态['listeners']):
            监听()

    def 取提示():
        '当前横幅'
        return 提示状态['state']

    def 订提示(监听):
        '横幅订阅'
        提示状态['listeners'].add(监听)
        def 退订():
            '卸下这一只'
            提示状态['listeners'].discard(监听)
        return 退订

    def 报告(结局):
        'pending 不弹。删成或失败各记一条'
        if 结局=='pending':
            return
        提示状态['seq']=提示状态['seq']+1
        种类='deleted' if 结局=='deleted' else 'deleteFailed'
        发布提示({'kind':种类,'seq':提示状态['seq']})

    def 关掉提示():
        '横幅自己倒计时结束'
        发布提示(None)

    删除提示源={
        'hooks':{'toast':{'getSnapshot':取提示,'subscribe':订提示}},
        'report':报告,
        'dismiss':关掉提示,
    }

    def 报告删除(原删除):
        '删除落定后走同一条横幅'
        def 包装(标识):
            '等删除返回再报告'
            结局=原删除(标识)
            报告(结局)
            return 结局
        return 包装

    def 删除目录项(标识):
        '按目录里的会话标识删除'
        快照=管理['hooks']['catalog'].getSnapshot()
        记录=None
        for 项 in 快照['records']:
            if 项['id']==标识:
                记录=项
                break
        if 记录 is None:
            return {'ok':True,'value':{'id':标识,'deleted':False,'code':'schedule_not_found'}}
        return 上下文.remote.schedule.delete({'sessionId':记录['sessionId'],'id':标识})

    def 订变更(监听):
        'schedule/changed'
        return getattr(上下文.remote,'$on')('schedule/changed',监听)

    def 订重置(监听):
        '连接重置'
        return 上下文.on('connection/reset',监听)

    def 列目录():
        '宿主任务目录'
        return 上下文.remote.schedule.catalog()

    管理=创建目录源({
        'list':列目录,
        'remove':删除目录项,
        'subscribeChanged':订变更,
        'subscribeReset':订重置,
    })

    def 更新任务(请求):
        '写入后若结果已定，按当时的读取序号再拉目录'
        结果=上下文.remote.schedule.update(请求)
        if 结果.get('ok') and ('record' in 结果.get('value',{}) or 结果.get('value',{}).get('code') in ('schedule_conflict','schedule_ended','schedule_not_found')):
            管理['onRetry'](管理['hooks']['catalog'].getSnapshot()['readRequest'])
        return 结果

    def 读历史(请求):
        '投递历史'
        return 上下文.remote.schedule.history(请求)

    def 打开会话(标识):
        '会话仍在且未归档才打开'
        if 会话链接状态(标识,上下文.sessions.list.getSnapshot(),上下文.workspaces.list.getSnapshot())=='available':
            上下文.uiWorkspace.openSession(标识)

    详情={
        'hooks':管理['hooks'],
        'onDelete':报告删除(管理['onDelete']),
        'onRetry':管理['onRetry'],
        'onUpdateTiming':更新任务,
        'loadHistory':读历史,
        'onOpenSession':打开会话,
    }

    def 活动页(会话标识):
        '这一会话还开着的页'
        return [页['id'] for 页 in 上下文.sidebarRight.tabsIn(会话标识)]

    绑定=任务标签绑定(活动页)

    def 登记横幅():
        '删除结果留在壳上'
        def 注入():
            '横幅只拿钩子和关掉'
            return {'hooks':删除提示源['hooks'],'dismiss':删除提示源['dismiss']}
        return 上下文.slots.register({
            'name':'shell.overlay','id':'schedule.delete-toast','locale':管理命名空间,'inject':注入,
        },删除提示)

    上下文.slots.inject('shell.overlay',登记横幅)

    def 登记种类():
        '右栏任务页种类。芯片在标题座位上再换成任务名'
        def 标题():
            '打开时的占位标题'
            return 管理中文['detail.label']
        return 上下文.sidebarRightTabs.register({
            'id':任务标识,'kind':任务种类,'priority':'builtin','title':标题,
        })

    上下文.effect(登记种类,'ui-schedule: task tab type')

    def 登记任务页():
        '右栏正文'
        def 注入():
            '详情动作加上页绑定'
            return {**详情,'taskBindings':绑定}
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab','key':任务标识,'locale':管理命名空间,'inject':注入,
        },日程任务标签)

    上下文.slots.inject('sidebar.right.pane.tab',登记任务页)

    def 登记任务标题():
        '右栏标题'
        def 注入():
            '标题只读目录和绑定'
            return {'hooks':详情['hooks'],'taskBindings':绑定}
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab.title','key':任务标识,'locale':管理命名空间,'inject':注入,
        },日程任务标签标题)

    上下文.slots.inject('sidebar.right.pane.tab.title',登记任务标题)

    def 登记任务管理():
        '主栏任务页。新建去开一条会话'
        def 注入():
            '详情动作加上新建会话'
            def 新建():
                '没有创建表'
                上下文.uiWorkspace.startSession()
            return {**详情,'onNewTask':新建}
        return 上下文.slots.register({
            'name':'main','key':面板标识,'locale':管理命名空间,'inject':注入,
        },任务管理页)

    上下文.slots.inject('main',登记任务管理)

    def 登记面板():
        '侧栏面板入口'
        def 标签():
            '面板名用中文表原文'
            return 管理中文['panel']
        return 上下文.slots.register({
            'name':'sidebar.panellist','id':面板标识,'order':10,'locale':管理命名空间,'label':标签,
        },任务管理图标)

    上下文.slots.inject('sidebar.panellist',登记面板)
    上下文.uiConversation.events.register(日程回合定义)

    def 登记回合卡():
        '回合尾的创建卡'
        def 注入(会话标识):
            '打开这一会话的任务页'
            def 打开详情(标识):
                '右栏按种类打开'
                上下文.sidebarRight.openTab(任务种类,{'params':{'sessionId':会话标识,'id':标识}})
            return {
                'hooks':{'catalog':管理['hooks']['catalog']},
                'onRetry':管理['onRetry'],
                'openTaskDetail':打开详情,
            }
        return 上下文.slots.register({
            'name':'conversation.chat.turnTail','id':'schedule-created','order':20,
            'locale':管理命名空间,'inject':注入,
        },日程回合卡)

    上下文.slots.inject('conversation.chat.turnTail',登记回合卡)

    def 登记页眉():
        '当前会话自己的活动提醒'
        def 注入(会话标识):
            '这一会话单独列活动任务'
            def 列出():
                '只列这一会话'
                return 上下文.remote.schedule.list({'sessionId':会话标识})
            def 删除(标识):
                '按这一会话删'
                return 上下文.remote.schedule.delete({'sessionId':会话标识,'id':标识})
            源=创建目录源({
                'list':列出,'remove':删除,'subscribeChanged':订变更,'subscribeReset':订重置,
            })
            def 打开详情(标识):
                '页眉和任务页打开同一张详情'
                上下文.sidebarRight.openTab(任务种类,{'params':{'sessionId':会话标识,'id':标识}})
            return {**源,'onDelete':报告删除(源['onDelete']),'openTaskDetail':打开详情}
        return 上下文.slots.register({
            'name':'conversation.session.header.utilities','id':'schedule-catalog','order':-5,
            'locale':命名空间,'inject':注入,
        },日程目录动作)

    上下文.slots.inject('conversation.session.header.utilities',登记页眉)

    def 注入目录():
        '可见行共用这一次目录'
        return {'hooks':{'catalog':管理['hooks']['catalog']}}

    def 登记标记():
        '会话行时钟'
        return 上下文.slots.register({
            'name':'sidebar.session.row.leading','id':'schedule-mark','order':10,
            'locale':命名空间,'inject':注入目录,
        },会话日程标记)

    上下文.slots.inject('sidebar.session.row.leading',登记标记)

    def 登记悬停():
        '悬停卡里的任务'
        return 上下文.slots.register({
            'name':'sidebar.session.row.hover','id':'schedule-tasks','order':10,
            'locale':命名空间,'inject':注入目录,
        },会话日程悬停)

    上下文.slots.inject('sidebar.session.row.hover',登记悬停)


apply=应用
