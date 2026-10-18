from uuid import uuid4 as 随机标识#审阅窗
from urllib.parse import quote as 网址编码#百分号编码
from ...存储 import 声明存储#审阅是否已经自动打开
from ...ui_基础界面组件.markdown.纯文本 import 抽取Markdown纯文本#临时审阅标题
from ....类型化远程调用.协议.异常 import 远程错误#历史在快照前结束
from ....类型化远程调用.协议.远程制品 import 取远程错误#识别远程失败
from . import 文案
from . import 计划
from . import 计划定义
from . import 审阅预览
from . import 计划卡
from . import 计划预览
from . import 计划芯片

__all__=[
    '文案','计划','计划定义','审阅预览','计划卡','计划预览','计划芯片',
    '命名空间','依赖','应用',
]

命名空间='plan'
预览标识='@deepseek-ai/dsh-client-ui-plan'
依赖=['slots','remote','remote.commands','remote.session','sessions','locale','uiConversation','resources','sidebarRight','sidebarRightTabs']


def 百分编码(文本):
    '对齐 encodeURIComponent'
    return 网址编码(str(文本),safe="-_.!~*'()")


def 应用(上下文,配置=None):
    '登记计划芯片、已提交计划卡、审阅打开和侧栏里的计划文档'
    def 登记词典():
        '登记本插件中英文案表。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})

    上下文.副作用(登记词典,'ui-plan: dictionaries')

    def 登记定义():
        '登记 submitted-plan'
        return 上下文.uiConversation.events.register(计划定义.计划定义)

    上下文.副作用(登记定义,'ui-plan: conversation definition')

    def 打开流(地址,选项):
        '同步逐帧读这份调用。找到就停。取消后不再产出'
        信号=选项['signal']

        def 已中止():
            '这份打开已经被取消'
            return 信号.is_set()

        if 已中止():
            return
        目标=计划.解析计划地址(地址)
        if 目标 is None:
            yield {
                'ok':False,
                'error':{
                    'code':'plan/invalid-address',
                    'message':'Invalid plan resource address.',
                    'details':{},
                },
            }
            return
        会话地址=目标['session']
        try:
            快照=None
            for 帧 in 上下文.remote.session.follow({'address':会话地址},信号):
                if 帧['type']=='snapshot':
                    快照=帧
                    break
            if 已中止():
                return
            if 快照 is None:
                raise 远程错误(
                    'plan/unavailable',
                    'Session history ended before the plan could be read.',
                    {},
                )
            页={'records':快照['records'],'hasMore':快照['hasMore']}
            while True:
                for 条目 in 页['records']:
                    一份=计划.已提交计划(条目['event'])
                    if 一份 is not None and 一份['callId']==目标['callId']:
                        yield {'ok':True,'value':一份}
                        return
                记录=页['records']
                前序=记录[0]['event']['seq'] if len(记录)>0 else None
                if not 页['hasMore'] or 前序 is None:
                    break
                下一=上下文.remote.session.page({
                    'address':会话地址,
                    'throughSeq':快照['cursor'],
                    'beforeSeq':前序,
                },信号)
                if 已中止():
                    return
                if 下一['ok'] is not True:
                    yield 下一
                    return
                页=下一['value']
            yield {
                'ok':False,
                'error':{
                    'code':'plan/not-found',
                    'message':'The submitted plan was not found in this Session.',
                    'details':{},
                },
            }
        except Exception as 错误:
            if 已中止():
                return
            远程=取远程错误(错误)
            if 远程 is not None:
                失败={'code':远程.code,'message':远程.message,'details':远程.details}
            else:
                失败={'code':'plan/read-failed','message':str(错误),'details':{}}
            yield {'ok':False,'error':失败}

    def 登记资源():
        '登记 plan 协议'
        return 上下文.resources.register({'protocol':'plan','open':打开流})

    上下文.副作用(登记资源,'ui-plan: resources')

    def 登记侧栏类型():
        '登记 plan 这种侧栏页'
        def 能否打开(地址):
            '计划地址或临时审阅地址才能开'
            return 计划.解析计划地址(地址) is not None or 审阅预览.是否审阅预览地址(地址)

        def 标题(地址=None):
            '类型标题。中文表原文是计划'
            return '计划'

        return 上下文.sidebarRightTabs.登记({
            'id':预览标识,
            'kind':'plan',
            'patterns':['dsh-resource://plan/**','dsh-resource://plan-review/**'],
            'priority':'builtin',
            'canOpen':能否打开,
            'title':标题,
        })

    上下文.副作用(登记侧栏类型,'ui-plan: sidebar type')

    def 打开(会话标识):
        '这个会话上打开一份已记录计划'
        def 打开计划(调用标识):
            '按会话和调用拼地址，再在右侧栏打开'
            子=上下文.sessions.subagentAddress(会话标识)
            if 子 is None:
                会话={'kind':'session','sessionId':会话标识}
            else:
                会话={
                    'kind':'subagent',
                    'parentSessionId':子['parentSessionId'],
                    'childSessionId':子['childSessionId'],
                    'mode':子['mode'],
                }
            if 会话['kind']=='session':
                段表=[会话['sessionId'],调用标识]
            else:
                段表=['subagent',会话['parentSessionId'],会话['childSessionId'],会话['mode'],调用标识]
            地址='dsh-resource://plan/'+'/'.join(百分编码(段) for 段 in 段表)
            上下文.sidebarRight.打开资源(地址)

        return {'openPlan':打开计划}

    审阅窗=str(随机标识())

    def 审阅初值():
        '还没有一份被自动打开过'
        return {'opened':{}}

    def 标记已打开(草稿,审阅键):
        '记下这个审阅已经自动打开'
        草稿['opened'][审阅键]=True

    审阅存储=声明存储({
        'init':审阅初值,
        'actions':{'markOpened':标记已打开},
    })

    def 登记回合尾():
        '登记已提交计划卡'
        def 注入(会话标识):
            '本会话的打开器，和这一回合的计划源'
            绑定=上下文.sessions.binding(会话标识)
            if 绑定 is None:
                raise Exception(f'ui-plan: unknown session "{会话标识}"')
            聊天=上下文.uiConversation.binding(绑定).target('chat')

            def 计划源(回合):
                '这一回合 submitted-plan 的可观察源'
                快照=聊天['getSnapshot']()
                if 快照 is None:
                    raise Exception('ui-plan: Chat target is unavailable')
                return 快照['nodes'].turnDataSource(int(回合),'submitted-plan')

            打开面=打开(会话标识)
            return {
                'openPlan':打开面['openPlan'],
                'keyedHooks':{'plans':计划源},
            }

        return 上下文.slots.register({
            'name':'conversation.chat.turnTail',
            'id':预览标识,
            'locale':命名空间,
            'inject':注入,
        },计划卡.计划卡)

    上下文.slots.inject('conversation.chat.turnTail',登记回合尾)

    def 登记审阅():
        '登记待审计划的打开器'
        def 注入(会话标识):
            '有调用标识就开已记录计划，否则开临时文档'
            def 打开审阅(审阅,请求键):
                '打开这份待审计划'
                if 审阅.get('callId') is not None:
                    打开(会话标识)['openPlan'](审阅['callId'])
                    return
                地址=f'dsh-resource://plan-review/{百分编码(会话标识)}/{百分编码(f"{审阅窗}:{请求键}")}'
                上下文.sidebarRight.打开资源(地址,{
                    'params':{
                        'planReview':{
                            'markdown':审阅['plan'],
                            'title':抽取Markdown纯文本(审阅['plan'],{'mode':'first-line'}),
                        },
                    },
                })

            return {
                'openReview':打开审阅,
                'hooks':{'sidebarMounted':上下文.sidebarRight.已挂载},
            }

        return 上下文.slots.register({
            'name':'conversation.plan-review.actions',
            'id':预览标识,
            'locale':命名空间,
            'store':审阅存储,
            'inject':注入,
        },计划卡.计划审阅打开)

    上下文.slots.inject('conversation.plan-review.actions',登记审阅)

    def 登记预览():
        '登记侧栏里的计划正文'
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab',
            'key':预览标识,
            'locale':命名空间,
        },计划预览.计划预览)

    上下文.slots.inject('sidebar.right.pane.tab',登记预览)

    def 登记标题():
        '登记侧栏标签上的计划标题'
        return 上下文.slots.register({
            'name':'sidebar.right.pane.tab.title',
            'key':预览标识,
        },计划预览.计划标题)

    上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)

    def 登记芯片():
        '登记输入栏上的计划芯片'
        def 注入(会话标识):
            '退出计划模式。失败句保持上游英文'
            def 退出():
                '执行 /plan off'
                结果=上下文.remote.commands.execute(会话标识,'/plan off',[])
                if 结果.get('ok') is not True:
                    错误=结果['error']
                    if isinstance(错误,dict):
                        消息=错误['message']
                        码=错误['code']
                    else:
                        消息=错误.message
                        码=错误.code
                    return f'{消息} ({码})'
                if 结果.get('value') is None:
                    return 'unknown command: /plan off'
                return None

            return {'exitPlanMode':退出}

        return 上下文.slots.register({
            'name':'conversation.input.plan',
            'locale':命名空间,
            'inject':注入,
        },计划芯片.计划芯片)

    上下文.slots.inject('conversation.input.plan',登记芯片)


inject=依赖
apply=应用
