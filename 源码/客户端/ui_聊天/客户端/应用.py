from ...模块.客户端.通告 import 取握手窗口
from ...存储 import 创建快照存储,声明存储
from ....工具.工作区路径 import 文件地址为
from ..聊天设置 import (
    聊天设置命名空间,
    默认链接打开,
    默认转录视图模式,
)
from ..异常 import 抛未知会话
from .文案 import 中文,英文,命名空间
from .转录视图 import 转录视图策略
from .呈现策略 import 导出呈现策略
from .性能用量 import 性能用量策略
from .约定.快照 import 空聊天快照
from .会话节点 import 登记会话节点
from .聊天.登记节点渲染器 import 登记聊天节点渲染器
from .聊天.聊天视图 import 聊天视图
from .聊天.聊天流程 import 聊天流程
from .聊天.用户内容 import 用户内容
from .聊天.统计行 import 活动胶囊,用量胶囊
from .聊天.配额须知宿主 import 配额须知宿主
from .聊天.审批命令 import 审批命令
from .设置.转录视图行 import 转录视图行
from .设置.链接打开行 import 链接打开行
from .设置.性能用量行 import 性能用量行
from .聊天.用回合数据 import 用回合数据值
from .聊天.用披露 import 绑定披露
from .聊天.流程动效 import 用流隐藏,用动效隐藏

__all__=['依赖','应用','聊天流注入','聊天节点注入']

依赖=[
    'slots','sessions','uiWorkspace','uiSession','uiConversation','locale',
    'configForms','remote','remote.session','sidebarRight',
]


def 组动作钩(标准,份额):
    '从这一次流的动效里取出组显隐'
    动效=份额.get('motion') if isinstance(份额,dict) else None

    def 用(隐藏,揭示):
        '绑到这一次视口'
        return 用流隐藏(隐藏,揭示,动效)

    return 用


def 组头动作钩(标准,份额):
    '从这一次流的动效里取出组头显隐'
    动效=份额.get('motion') if isinstance(份额,dict) else None

    def 用(引用,隐藏):
        '绑到组头'
        用动效隐藏(引用,隐藏,动效)

    return 用


聊天流注入={
    'hooks':{
        'groupAction':组动作钩,
        'groupHeaderAction':组头动作钩,
    },
}


def 回合数据钩(标准,份额):
    '节点本地的回合数据'
    数据=份额.get('turnData') if isinstance(份额,dict) else None

    def 用(键):
        '按键读这一回合的数据'
        return 用回合数据值(数据,键)

    return 用


def 披露钩(标准,份额):
    '把披露重置绑成钩子'
    重置=份额.get('disclosureReset') if isinstance(份额,dict) else None
    return 绑定披露(重置)


def 组动作转发(标准,份额):
    '沿用流已经准备好的组显隐钩'
    if isinstance(份额,dict):
        return 份额.get('useGroupAction')
    return None


聊天节点注入={
    'hooks':{
        'turnData':回合数据钩,
        'disclosure':披露钩,
        'groupAction':组动作转发,
    },
}


def 创建聊天存储():
    '每份渲染中的会话一份手动展开记录'
    def 初始():
        '没有手动展开记录'
        return {'turnProcesses':[]}

    def 设置回合过程打开(草稿,回合,回答步,打开):
        '记下这一代回答是展开还是收起'
        下标=-1
        序号=0
        for 条目 in 草稿['turnProcesses']:
            if 条目['turn']==回合:
                下标=序号
                break
            序号+=1
        if 打开:
            下一条={'turn':回合,'answerStep':回答步}
        else:
            下一条={'turn':回合,'answerStep':回答步,'collapsed':True}
        if 下标<0:
            草稿['turnProcesses'].append(下一条)
        else:
            草稿['turnProcesses'][下标]=下一条

    return 声明存储({
        'init':初始,
        'actions':{'setTurnProcessOpen':设置回合过程打开},
    })


def 应用(上下文,配置=None):
    '登记聊天目标、渲染器、统计和额度须知'
    额度须知=创建快照存储(None)
    额度序号=0
    额度持有=set()
    聊天源表={}
    额度订阅=set()

    def 拆额度():
        '拆掉还活着的额度订阅'
        for 拆 in list(额度订阅):
            拆()

    上下文.副作用(拆额度,'ui-chat: live quota notices')

    def 聊天源(绑定):
        '一份会话绑定一份聊天快照源。额度失败只在新追加时公布'
        标识=id(绑定)
        if 标识 in 聊天源表:
            return 聊天源表[标识]

        def 听追加():
            '只把新追加的额度错误收成一条全窗口须知'
            nonlocal 额度序号
            快照=绑定.eventSource.getSnapshot()
            变化=快照.get('change') if isinstance(快照,dict) else None
            if not isinstance(变化,dict) or 变化.get('kind')!='append':
                return
            for 项 in 变化.get('entries') or []:
                事件=项.get('event') if isinstance(项,dict) else None
                if not isinstance(事件,dict) or 事件.get('type')!='turn/end':
                    continue
                数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
                原因=数据.get('reason') if isinstance(数据.get('reason'),dict) else {}
                if 原因.get('kind')!='error':
                    continue
                错误=原因.get('error') if isinstance(原因.get('error'),dict) else {}
                码=错误.get('code')
                if len(额度持有)>0 or 码 not in ('QUOTA','ACCOUNT_QUOTA'):
                    continue
                额度序号+=1
                额度须知.set({'code':码,'seq':额度序号})

        def 挂额度():
            '绑定还在就听事件源'
            停止=绑定.eventSource.subscribe(听追加)

            def 拆():
                '停止监听并忘掉这份源'
                停止()
                if 标识 in 聊天源表:
                    del 聊天源表[标识]
                额度订阅.discard(拆)

            return 拆

        拆=绑定.ctx.副作用(挂额度,'ui-chat: Provider binding quota notices')
        额度订阅.add(拆)
        目标=上下文.uiConversation.binding(绑定).target('chat')

        def 取快照():
            '没有构建器时用空聊天快照'
            快照=目标.getSnapshot()
            return 空聊天快照 if 快照 is None else 快照

        def 订阅(监听):
            '跟目标的快照'
            return 目标.subscribe(监听)

        源={'getSnapshot':取快照,'subscribe':订阅}
        聊天源表[标识]=源
        return 源

    登记会话节点(上下文)

    def 解析会话(绑定):
        '每个会话提供一份聊天快照钩子'
        return {'hooks':{'chat':聊天源(绑定)}}

    上下文.uiSession.provide({'hooks':['chat'],'resolve':解析会话})

    def 登记词典():
        '登记本包中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})

    上下文.副作用(登记词典,'ui-chat: dictionaries')
    聊天存储=创建聊天存储()
    滚动位置={}
    聊天设置=上下文.configForms.get(聊天设置命名空间)
    初始打开=聊天设置.getSnapshot()
    初始值=初始打开.get('value') if isinstance(初始打开,dict) else None
    打开=初始值.get('linkOpening') if isinstance(初始值,dict) and 初始值.get('linkOpening') is not None else 默认链接打开
    链接打开=创建快照存储(打开)

    def 同步打开():
        '宿主接受的打开方式写回本地'
        快照=聊天设置.getSnapshot()
        值=快照.get('value') if isinstance(快照,dict) else None
        已接受=值.get('linkOpening') if isinstance(值,dict) else None
        if 已接受 is not None:
            链接打开.set(已接受)

    def 订打开():
        '宿主打开方式变化时写回本地'
        return 聊天设置.subscribe(同步打开)

    上下文.副作用(订打开,'ui-chat: link opening')

    def 等浏览器页签(范围):
        '有右侧浏览器页签时才登记链接打开方式'
        页签=范围.sidebarRightTabs

        def 浏览器在():
            '浏览器页签有没有登记'
            return 页签.get('browser') is not None

        def 订浏览器(监听):
            '跟页签表'
            return 页签.subscribe(监听)

        浏览器可用={'getSnapshot':浏览器在,'subscribe':订浏览器}

        def 设打开(目的地):
            '先改本地，再写宿主。写失败也留着这次选择'
            链接打开.set(目的地)
            try:
                聊天设置.set('linkOpening',目的地)
            except Exception:
                return

        def 注入():
            '链接打开行要的钩子'
            return {
                'hooks':{'linkOpening':链接打开,'browserAvailable':浏览器可用},
                'setLinkOpening':设打开,
            }

        def 登记():
            '通用设置里的链接打开行'
            return 范围.slots.register({
                'name':'settings.general.item',
                'id':'link-opening',
                'order':17,
                'locale':命名空间,
                'inject':注入,
            },链接打开行)

        return 范围.slots.inject('settings.general.item',登记)

    上下文.依赖启动(['sidebarRightTabs'],等浏览器页签)
    窗=取握手窗口()
    桌面=窗['dshDesktop'] is True
    转录=转录视图策略(聊天设置,'standard' if 桌面 else 默认转录视图模式)
    呈现=导出呈现策略(转录.mode,转录.collapseTiming)
    性能=性能用量策略(聊天设置)

    def 拆策略():
        '拆掉两份已接受值订阅'
        转录.dispose()
        性能.dispose()

    上下文.副作用(拆策略)
    性能用量=性能.mode
    登记聊天节点渲染器(上下文,性能用量,呈现)
    上下文.slots.registerFactory({
        'name':'conversation.chat.user.content',
        'scope':'session',
        'locale':命名空间,
        'children':{'conversation.chat.user.images':{'kind':'single','scope':'session'}},
    },用户内容)

    def 设性能(模式):
        '改性能与用量档'
        性能.setMode(模式)

    def 性能注入():
        '性能行要的钩子'
        return {'hooks':{'performanceUsage':性能用量},'setPerformanceUsage':设性能}

    def 挂性能():
        '通用设置里的性能行'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'performance-usage',
            'order':30,
            'locale':命名空间,
            'inject':性能注入,
        },性能用量行)

    上下文.slots.inject('settings.general.item',挂性能)

    def 设转录(模式):
        '改工作步骤展示'
        转录.setMode(模式)

    def 设收起(时机):
        '改收起时机'
        转录.setCollapseTiming(时机)

    def 转录注入():
        '转录行要的钩子'
        return {
            'hooks':{'transcriptView':转录.mode,'collapseTiming':转录.collapseTiming},
            'setTranscriptView':设转录,
            'setCollapseTiming':设收起,
        }

    def 挂转录():
        '通用设置里的工作步骤行'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'transcript-view',
            'order':12,
            'locale':命名空间,
            'inject':转录注入,
        },转录视图行)

    上下文.slots.inject('settings.general.item',挂转录)

    def 节点源(绑定):
        '这一份绑定上的聊天节点和组'
        聊天=聊天源(绑定)
        会话=上下文.uiConversation.binding(绑定)

        def 节点(键):
            '单个节点源'
            return 聊天['getSnapshot']().nodes.source(键)

        def 底(键):
            '贴底源'
            return 聊天['getSnapshot']().nodes.bottomSource(键)

        def 过程(键):
            '过程源'
            return 聊天['getSnapshot']().nodes.processSource(键)

        def 组(键):
            '会话组源'
            快照=会话.snapshot.getSnapshot()
            视图=快照.get('views') if isinstance(快照,dict) else None
            分组=视图.grouped('chat') if hasattr(视图,'grouped') else None
            if 分组 is None:
                return None
            return 分组.groupSource(键)

        return {
            'hooks':{'presentation':呈现},
            'keyedHooks':{
                'chatNode':节点,
                'chatNodeBottom':底,
                'chatNodeProcess':过程,
                'chatGroup':组,
            },
        }

    def 挂流():
        '聊天流。未知会话直接失败'

        def 注入(会话标识):
            '按会话取节点源'
            绑定=上下文.sessions.binding(会话标识)
            if 绑定 is None:
                抛未知会话(会话标识)
            return 节点源(绑定)

        return 上下文.slots.register({
            'name':'conversation.chat.flow',
            'locale':命名空间,
            'store':聊天存储,
            'children':{
                'conversation.chat.node':{'kind':'keyed','scope':'session','inject':聊天节点注入},
            },
            'inject':注入,
        },聊天流程)

    上下文.slots.inject('conversation.chat.flow',挂流)

    def 挂视图():
        '对话视图里的聊天'

        def 视图标签():
            '页签标题用中文表原文'
            return 中文['view.chat']

        def 注入(会话标识):
            '打开文件、外链、历史和分支都从这里出去'
            绑定=上下文.sessions.binding(会话标识)
            if 绑定 is None:
                抛未知会话(会话标识)
            会话=绑定.session
            聊天=聊天源(绑定)
            源=节点源(绑定)

            def 文件提及(业主):
                '收束回合的文件提及'
                服务=上下文.获取服务('chatFileMentions',False)
                if 服务 is None:
                    return None
                return 服务.forClosing(业主,会话标识)

            def 打开文件(路径,选项=None):
                '文件进右侧栏。行号是导航参数'
                列表=上下文.sessions.list.getSnapshot()
                按标识=列表.get('byId') if isinstance(列表,dict) else {}
                记录=按标识.get(会话标识) if isinstance(按标识,dict) else None
                工作目录=记录.get('cwd') if isinstance(记录,dict) else None
                地址=文件地址为(会话标识,工作目录,路径)
                if not isinstance(选项,dict) or 选项.get('line') is None:
                    上下文.sidebarRight.openResource(地址)
                else:
                    上下文.sidebarRight.openResource(地址,{'params':{'line':选项['line']}})

            def 打开外链(网址):
                '侧栏浏览器在，并且偏好是侧栏，就在侧栏打开'
                页签=上下文.获取服务('sidebarRightTabs',False)
                有浏览器=页签 is not None and 页签.get('browser') is not None
                if 链接打开.getSnapshot()=='sidebar' and 有浏览器:
                    上下文.sidebarRight.openTab('browser',{'params':{'url':网址}})
                else:
                    取握手窗口().open(网址,'_blank','noopener,noreferrer')

            def 加载更早():
                '再取一页更早的历史'
                会话.loadOlder()

            def 加载直到(序号):
                '加载到这一条'
                return 会话.loadThrough(序号)

            def 加载图片(附件):
                '按会话取图片地址'
                return 上下文.uiConversation.imageUrl(会话标识,附件)

            def 看图片(附件):
                '已经有的图片地址'
                return 上下文.uiConversation.peekImageUrl(会话标识,附件)

            加载图片.peek=看图片

            def 保存滚动(位置):
                '离开时记下滚动。空位置就忘掉'
                if 位置 is None:
                    if 会话标识 in 滚动位置:
                        del 滚动位置[会话标识]
                else:
                    滚动位置[会话标识]=位置

            def 读取滚动():
                '回来时读上次的位置'
                return 滚动位置.get(会话标识)

            def 在此分支(序号):
                '从已完成回合分出新会话。失败就留在原视图'
                快照=聊天['getSnapshot']()
                时间线=快照.get('timeline') if isinstance(快照,dict) else {}
                回合表=时间线.get('turns') if isinstance(时间线,dict) else {}
                消息标识=None
                if isinstance(回合表,dict):
                    for 回合 in 回合表.values():
                        结束=回合.get('end') if isinstance(回合,dict) else None
                        if isinstance(结束,dict) and 结束.get('seq')==序号:
                            数据=回合.get('data')
                            尾=数据.get('turn-tail') if hasattr(数据,'get') else None
                            收束=尾.get('closing') if isinstance(尾,dict) else None
                            终=收束.get('finalNode') if isinstance(收束,dict) else None
                            if isinstance(终,dict):
                                消息标识=终.get('messageId')
                try:
                    子标识=上下文.sessions.fork({
                        'sessionId':会话标识,
                        'atSeq':序号,
                        'increaseTitle':True,
                    })
                    上下文.uiWorkspace.openSession(子标识)
                    分析=上下文.获取服务('productAnalytics',False)
                    if 分析 is not None:
                        载荷={'session_id':子标识,'parent_session_id':会话标识,'click_position':'footer'}
                        if 消息标识 is not None:
                            载荷['parent_message_id']=消息标识
                        分析.track('branch_session_click',载荷)
                except Exception:
                    return

            源['fileMentions']=文件提及
            源['openFile']=打开文件
            源['openExternalLink']=打开外链
            源['loadOlder']=加载更早
            源['loadThrough']=加载直到
            源['loadImage']=加载图片
            源['chatScroll']={'save':保存滚动,'read':读取滚动}
            源['forkAt']=在此分支
            return 源

        return 上下文.slots.register({
            'name':'conversation.view',
            'id':'chat',
            'order':0,
            'label':视图标签,
            'locale':命名空间,
            'children':{
                'conversation.chat.flow':{'kind':'single','scope':'session','inject':聊天流注入},
            },
            'store':聊天存储,
            'inject':注入,
        },聊天视图)

    上下文.slots.inject('conversation.view',挂视图)

    def 挂须知():
        '额度须知挂在全窗口遮罩上'

        def 关掉():
            '清掉持有并收起须知'
            额度持有.clear()
            额度须知.set(None)

        def 保持打开():
            '没有活须知就不再持有。有的话返回释放这一次持有的函数'
            if 额度须知.getSnapshot() is None:
                def 空释放():
                    '没有须知可留'
                    return
                return 空释放
            令牌=object()
            额度持有.add(令牌)

            def 释放():
                '只释放这一次持有'
                额度持有.discard(令牌)

            return 释放

        def 注入():
            '须知宿主要的钩子'
            return {
                'hooks':{'notice':额度须知},
                'dismissNotice':关掉,
                'keepNoticeOpen':保持打开,
            }

        return 上下文.slots.register({
            'name':'shell.overlay',
            'id':'chat.quota-notice',
            'locale':命名空间,
            'children':{'shell.quota-notice':{'kind':'chain','scope':'root'}},
            'inject':注入,
        },配额须知宿主)

    上下文.slots.inject('shell.overlay',挂须知)

    def 统计注入():
        '两颗胶囊共用用量档'
        return {'hooks':{'performanceUsage':性能用量}}

    def 挂坞():
        '活动胶囊和用量胶囊各占一个坞位'
        yield 上下文.slots.register({
            'name':'conversation.composer.dock',
            'id':'activity',
            'order':0,
            'locale':命名空间,
            'inject':统计注入,
        },活动胶囊)
        yield 上下文.slots.register({
            'name':'conversation.composer.dock',
            'id':'usage',
            'order':1,
            'locale':命名空间,
            'inject':统计注入,
        },用量胶囊)

    上下文.slots.inject('conversation.composer.dock',挂坞)

    def 挂审批():
        '审批详情用命令卡'
        def 登记():
            '登记审批详情'
            return 上下文.slots.register({'name':'conversation.approval.detail'},审批命令)
        return 上下文.slots.inject('conversation.approval.detail',登记)

    上下文.副作用(挂审批,'ui-chat: approval detail')


apply=应用
