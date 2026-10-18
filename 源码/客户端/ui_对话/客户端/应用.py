'登记与目标无关的会话装配、外壳、输入和停靠'
import pywebbridge
from ....上下文.文件引用.词法 import 格式化文件提及
from ....工具.工作区路径 import 工作区标题自,相对化到工作目录
from ...ui_基础界面组件.icons import 图标回形针16
from ...ui_槽位 import 解析槽标签
from ...存储 import 创建快照存储
from ..提交设置 import 会话设置命名空间
from ..异常 import 不支持图片媒体类型,对话错误
from .文案 import 命名空间,中文,英文
from .存储 import 创建会话存储,读会话视图偏好
from .服务 import 会话控制器,是图片媒体类型
from .视图选中项 import 轨迹视图标识,解析活动视图
from .停止快捷键 import 安装停止快捷键
from .会话.装配 import 界面会话
from .用户文本.用户文本 import 用户文本,纯文本,会话引用
from .用户文本.会话引用规则 import 会话引用规则
from .用户文本.空白字符规则 import 折叠空白规则,修剪空白规则
from .输入.阻断 import 撰写器阻断登记表
from .输入.枢纽 import 输入枢纽
from .输入.提交策略 import 提交策略
from .队列.队列停靠 import 队列停靠条目
from .设置.回车行为行 import 回车行为行
from .骨架.会话根 import 会话根
from .骨架.会话体 import 会话体
from .骨架.会话面板 import 会话面板
from .骨架.会话报头 import 会话报头
from .骨架.会话 import 会话,会话页眉
from .骨架.输入栏 import 输入栏
from .骨架.待办面板 import 待办停靠条目

__all__=['依赖','配置','应用']

依赖=[
    'slots','sessions','fileUpload','uiSession','uiWorkspace','locale','configForms',
]

def 配置(原始=None):
    '并发文件上传数，缺省 2，至少 1'
    值=2
    if isinstance(原始,dict) and 原始.get('maxConcurrentFileUploads') is not None:
        值=原始['maxConcurrentFileUploads']
    if not isinstance(值,int) or isinstance(值,bool) or 值<1:
        raise 对话错误('ui-conversation: maxConcurrentFileUploads must be a natural number')
    return {'maxConcurrentFileUploads':值}

def 空快照():
    '缺席源快照'
    return None

def 空订(回调):
    '缺席源不通知'
    return lambda: None

缺席通知={'getSnapshot':空快照,'subscribe':空订}
缺席阻断={'getSnapshot':lambda: None,'subscribe':空订}
空词表={}
缺席词表={'getSnapshot':lambda: 空词表,'subscribe':空订}
缺席菜单={'getSnapshot':空快照,'subscribe':空订}
空上传={}
缺席上传={'getSnapshot':lambda: 空上传,'subscribe':空订}

def 应用(上下文,配置值=None):
    '挂上会话核心和与目标无关的呈现'
    if 配置值 is None:
        配置值=配置({})
    elif not isinstance(配置值,dict) or 'maxConcurrentFileUploads' not in 配置值:
        配置值=配置(配置值)
    并发=配置值['maxConcurrentFileUploads']
    会话面=上下文.sessions
    槽=上下文.slots
    工作区导航=上下文.get('uiWorkspace')
    界面=界面会话(上下文,会话面)
    界面.userText.register(会话引用规则)
    界面.userText.register(折叠空白规则)
    界面.userText.register(修剪空白规则)
    def 用户文本注入():
        '规则修订和求值器'
        def 上报(错误):
            '变换失败写到控制台，原文仍整段保留'
            print('[ui-conversation] user-text transformation failed:',错误)
        return {
            'hooks':{
                'userTextRevision':{
                    'getSnapshot':界面.userText.getSnapshot,
                    'subscribe':界面.userText.subscribe,
                },
            },
            'createUserTextEvaluator':界面.userText.createEvaluator,
            'reportTransformFailure':上报,
        }
    槽.registerFactory({
        'name':'conversation.user.text',
        'scope':'session',
        'children':{
            'conversation.user.text.node':{'kind':'keyed','scope':'session','inline':True},
        },
        'inject':用户文本注入,
    },用户文本)
    def 登记文本节点():
        '纯文本和会话引用两个键'
        yield 槽.register({'name':'conversation.user.text.node','key':'text','priority':100},纯文本)
        yield 槽.register({'name':'conversation.user.text.node','key':'session','priority':100},会话引用)
    槽.inject('conversation.user.text.node',登记文本节点)
    def 登记词典():
        '登记中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.effect(登记词典,'ui-conversation: dictionaries')
    翻译=上下文.locale.bind(命名空间)
    会话存储=创建会话存储()
    提交=提交策略(上下文.configForms.get(会话设置命名空间))
    def 拆提交():
        '释放偏好订阅'
        def 拆():
            '拆掉设置订阅'
            提交.释放()
        return 拆
    上下文.effect(拆提交)
    def 回车注入():
        '忙碌回车钩子和写入'
        return {'hooks':{'busyEnter':提交.忙碌回车},'setBusyEnter':提交.设置忙碌回车}
    def 登记回车行():
        '通用设置里的忙碌回车行'
        return 槽.register({
            'name':'settings.general.item',
            'id':'composer-enter',
            'order':20,
            'locale':命名空间,
            'inject':回车注入,
        },回车行为行)
    槽.inject('settings.general.item',登记回车行)
    def 视图页签():
        '已登记视图。开发者工具关掉时不列出轨迹'
        页=[]
        开发=上下文.configForms.developerTools.enabled.getSnapshot()
        for 条目 in 槽.entries('conversation.view'):
            选项=条目['options'] if 'options' in 条目 else 条目
            if 选项.get('id') is None:
                continue
            if (not 开发) and 选项['id']==轨迹视图标识:
                continue
            标签=解析槽标签(选项.get('label'))
            页.append({'id':选项['id'],'label':选项['id'] if 标签 is None else 标签})
        return 页
    def 激活视图(会话标识,偏好):
        '把解析出的视图交给这份绑定'
        活动=解析活动视图(视图页签(),偏好)
        if 活动 is not None:
            界面.binding(会话标识).activate(活动['id'])
    def 恢复视图(会话标识):
        '按存下的偏好恢复'
        激活视图(会话标识,读会话视图偏好(会话标识))
    视图存储=创建快照存储(视图页签())
    绑定集=set()
    已跟踪=set()
    def 跟踪绑定(绑定):
        '每份绑定只记一次，作用域结束时摘掉'
        标识=id(绑定)
        if 标识 in 已跟踪:
            return
        已跟踪.add(标识)
        绑定集.add(绑定)
        def 拆绑():
            '作用域结束时从活动集合拿掉'
            def 摘():
                '摘掉这份绑定'
                绑定集.discard(绑定)
            return 摘
        绑定.ctx.effect(拆绑,'ui-conversation: active Provider binding')
    def 刷新视图():
        '页签变了就发布，并给每份绑定恢复视图'
        当前=视图存储.getSnapshot()
        下一=视图页签()
        未变=len(当前)==len(下一)
        if 未变:
            下标=0
            while 下标<len(当前):
                候选=下一[下标]
                页=当前[下标]
                if 候选['id']!=页['id'] or 候选['label']!=页['label']:
                    未变=False
                    break
                下标+=1
        if not 未变:
            视图存储.set(下一)
        for 绑定 in list(绑定集):
            恢复视图(绑定.sessionId)
    def 订视图():
        '视图登记、语言和开发者工具变化时刷新'
        拆视图=槽.subscribe('conversation.view',刷新视图)
        拆语言=上下文.locale.subscribe(刷新视图)
        拆开发=上下文.configForms.developerTools.enabled.subscribe(刷新视图)
        def 拆():
            '逆序拆掉这三份订阅'
            拆开发()
            拆语言()
            拆视图()
        return 拆
    上下文.effect(订视图,'ui-conversation: View selection')
    def 停止(会话标识):
        '取消当前回合。失败由会话的 promptError 发布'
        try:
            作用域=会话面.scope(会话标识)
            if 作用域 is None:
                raise 对话错误('ui-conversation: session "'+str(会话标识)+'" resolved no scope')
            会话服务=作用域.get('conversation')
            if 会话服务 is None:
                raise 对话错误('ui-conversation: conversation service unavailable through the session scope')
            结果=会话服务.cancel()
            if hasattr(结果,'等待'):
                结果.等待()
        except Exception:
            return
    停止快捷存储=创建快照存储([])
    def 装快捷键(范围):
        '登记固定输入，并把停止序列接到当前回合'
        固定=[
            {'id':'fixed.send','label':lambda: 中文['input.send'],'keys':['Enter'],'bindings':[{'code':'Enter','modifiers':[]}],'group':'input'},
            {'id':'fixed.newline','label':lambda: 中文['shortcut.newline'],'keys':范围.shortcuts.describeBinding({'code':'Enter','modifiers':['shift']})['keys'],'bindings':[{'code':'Enter','modifiers':['shift']}],'group':'input'},
            {'id':'fixed.complementary','label':lambda: 中文['shortcut.complementary'],'keys':范围.shortcuts.describeBinding({'code':'Enter','modifiers':['primary']})['keys'],'bindings':[{'code':'Enter','modifiers':['control']},{'code':'Enter','modifiers':['meta']}],'group':'input'},
            {'id':'fixed.slash','label':lambda: 中文['shortcut.slash'],'keys':['/'],'bindings':[{'code':'Slash','modifiers':[]}],'group':'input'},
            {'id':'fixed.mention','label':lambda: 中文['shortcut.mention'],'keys':['@'],'bindings':[{'code':'Digit2','modifiers':['shift']}],'group':'input'},
        ]
        for 命令 in 固定:
            def 挂(命令=命令):
                '登记这一条固定命令'
                return 范围.shortcuts.registerFixed(命令)
            范围.effect(挂,'ui-conversation: '+命令['id'])
        def 挂停止():
            '把 Escape 序列接到停止'
            return 安装停止快捷键(范围.shortcuts,会话面,lambda 绑定:界面.binding(绑定).openTurn,上下文.uiSession,停止)
        范围.effect(挂停止,'ui-conversation: fixed stop input')
        def 挂停止参照():
            '发布停止快捷键的显示键'
            命令={'id':'response.stop','label':lambda: 中文['input.stop'],'keys':['Esc','Esc'],'bindings':[{'code':'Escape','modifiers':[]}],'group':'input'}
            拆=范围.shortcuts.registerFixed(命令)
            停止快捷存储.set(命令['keys'])
            def 拆参照():
                '清空显示键并拆登记'
                停止快捷存储.set([])
                拆()
            return 拆参照
        范围.effect(挂停止参照,'ui-conversation: fixed stop reference')
    上下文.inject(['shortcuts'],装快捷键)
    枢纽=输入枢纽(上下文,翻译)
    阻断表=撰写器阻断登记表()
    def 登记文件(范围):
        '等 commandUi 后登记 file 动作'
        命令面=范围.get('commandUi')
        def 挂文件():
            '回形针打开文件选择'
            def 可用(会话):
                '撰写器是否接受文件'
                return 枢纽.canPickFiles(会话['sessionId'])
            def 执行(会话):
                '打开文件选择'
                枢纽.pickFiles(会话['sessionId'])
            return 命令面.register({
                'name':'file',
                'label':lambda: 中文['input.file'],
                'icon':图标回形针16,
                'available':可用,
                'ui':{'kind':'action','run':执行},
            })
        范围.effect(挂文件,'ui-conversation: File action')
    上下文.inject(['commandUi'],登记文件)
    def 提供输入():
        '向会话作用域提供 conversation 和 input'
        def 解析(绑定):
            '这份绑定的快照和动作'
            跟踪绑定(绑定)
            壳=枢纽.shellFor(绑定)
            对话绑定=界面.binding(绑定)
            恢复视图(绑定.sessionId)
            return {
                'hooks':{'conversation':对话绑定.snapshot,'input':壳.state},
                'props':{'inputActions':壳.actions},
            }
        return 上下文.uiSession.provide({
            'hooks':['conversation','input'],
            'props':['inputActions'],
            'resolve':解析,
        })
    上下文.effect(提供输入,'ui-conversation: input standard-kit provider')
    def 具体会话():
        '公开服务转成控制器'
        会话=上下文.get('conversation')
        if 会话 is None:
            raise 对话错误('ui-conversation: conversation service unavailable')
        return 会话
    def 根注入(会话标识):
        '阻断源。切换工作区前迁移草稿'
        def 选定工作区(工作区标识):
            '打开前把草稿和附件带到下一会话'
            def 打开前(下一标识):
                '跨会话迁移。拒收附件就停下'
                if 会话标识 is not None and 下一标识!=会话标识:
                    旧=枢纽.shell(会话标识)
                    草稿=旧.draftSnapshot
                    附件=旧.snapshot['attachmentIds']
                    新=枢纽.shell(下一标识)
                    if len(附件)==0 or 新.addAttachments(附件):
                        if 会话面.binding(下一标识) is None:
                            raise 对话错误('ui-conversation: session "'+str(下一标识)+'" resolved no binding')
                        具体会话().rebindDraftFiles(下一标识,附件)
                        if 草稿['text']!='':
                            新.setDraft(草稿)
                            旧.setDraft('')
                        if len(附件)>0:
                            for 标识 in 附件:
                                旧.removeAttachment(标识)
            工作区导航.openWorkspace(工作区标识,打开前)
        return {
            'hooks':{'composerBlock':缺席阻断 if 会话标识 is None else 阻断表.storeFor(会话标识)},
            'selectWorkspace':选定工作区,
        }
    def 登记根():
        'main.conversation 只声明页眉子槽'
        return 槽.register({
            'name':'main.conversation',
            'children':{'conversation.header':{'kind':'single','scope':'session-maybe'}},
        },会话根)
    def 登记体():
        '内容工厂。子槽含会话、链、栏、停靠和英雄'
        return 槽.registerFactory({
            'name':'conversation.content',
            'scope':'session-maybe',
            'locale':命名空间,
            'children':{
                'conversation.session':{'kind':'single','scope':'session'},
                'conversation.composer':{'kind':'chain','scope':'session'},
                'conversation.composer.bar':{'kind':'single','scope':'session-maybe'},
                'conversation.input.dock':{'kind':'list','scope':'session'},
                'conversation.hero.brand.mark':{'kind':'single','scope':'root'},
                'conversation.hero.workspace':{'kind':'single','scope':'root'},
                'conversation.hero.agentPreset':{'kind':'single','scope':'session-maybe'},
                'conversation.hero.options':{'kind':'list','scope':'session'},
            },
            'slots':{'views':{'scope':'session'},'widthControls':{'scope':'root'}},
            'inject':根注入,
        },会话体)
    def 登记会话():
        '严格会话体。视图环和检视'
        def 注入(会话标识,动作):
            '打开视图、检视调用和草稿持久化'
            def 打开视图(视图,焦点):
                '视图已登记才激活并记下焦点'
                if not any(页['id']==视图 for 页 in 视图页签()):
                    return
                激活视图(会话标识,视图)
                动作['openView'](视图,焦点)
            def 检视目标():
                '第一个带工具焦点、且页签里有的视图定义'
                for 定义 in 界面.views.entries():
                    if 定义.get('toolCallFocus') is not None and any(页['id']==定义['target'] for 页 in 视图存储.getSnapshot()):
                        return 定义
                return None
            def 检视调用(调用标识):
                '打开那个视图并聚焦这次调用'
                目标=检视目标()
                if 目标 is not None and 目标.get('toolCallFocus') is not None:
                    打开视图(目标['target'],目标['toolCallFocus'](调用标识))
            def 检视快照():
                '没有检视目标时钩子是 None'
                if 检视目标() is None:
                    return None
                return 检视调用
            def 订检视(监听):
                '视图或定义变了都通知'
                拆视图=视图存储.subscribe(监听)
                拆定义=界面.views.subscribe(监听)
                def 拆():
                    '两份都拆'
                    拆视图()
                    拆定义()
                return 拆
            return {
                'hooks':{
                    'conversationViews':视图存储,
                    'inspectCall':{'getSnapshot':检视快照,'subscribe':订检视},
                },
                'bindDraftPersistence':lambda 写出:枢纽.shell(会话标识).bindDraftPersistence(写出),
                'openView':打开视图,
            }
        return 槽.register({
            'name':'conversation.session',
            'children':{'conversation.view':{'kind':'list','scope':'session'}},
            'store':会话存储,
            'inject':注入,
        },会话)
    def 登记页眉():
        '常驻页眉。前导和会话页眉'
        return 槽.register({
            'name':'conversation.header',
            'children':{
                'conversation.header.leading':{'kind':'single','scope':'root'},
                'conversation.session.header':{'kind':'single','scope':'session'},
            },
        },会话报头)
    def 登记会话页眉():
        '谱系、动作、工具和角标。谱系是 single'
        def 注入(会话标识,动作):
            '视图环、打开会话和选择视图'
            def 选择(视图):
                '激活并写入存储'
                激活视图(会话标识,视图)
                动作['setView'](视图)
            return {
                'hooks':{'conversationViews':视图存储},
                'open':lambda 标识:工作区导航.openSession(标识),
                'selectView':选择,
            }
        return 槽.register({
            'name':'conversation.session.header',
            'locale':命名空间,
            'children':{
                'conversation.session.header.lineage':{'kind':'single','scope':'session'},
                'conversation.session.header.actions':{'kind':'list','scope':'session'},
                'conversation.session.header.utilities':{'kind':'list','scope':'session'},
                'conversation.session.header.corner':{'kind':'single','scope':'session'},
            },
            'store':会话存储,
            'inject':注入,
        },会话页眉)
    def 登记栏():
        '撰写器栏。无会话时给静态空源'
        def 注入(会话标识):
            '键盘、加文件、停止和外部钩子'
            if 会话标识 is None:
                return {
                    'keyboard':None,
                    'addFiles':None,
                    'removeAttachment':None,
                    'resolveDraftAttachments':None,
                    'retryFileUpload':None,
                    'toggleCommandMenu':None,
                    'stop':None,
                    'hooks':{
                        'stopShortcut':停止快捷存储,
                        'busyEnter':提交.忙碌回车,
                        'fileUploads':缺席上传,
                        'notices':缺席通知,
                        'lexicon':缺席词表,
                        'menuLauncher':缺席菜单,
                    },
                }
            控制器=具体会话()
            壳=枢纽.shell(会话标识)
            触发=枢纽.inputTriggers(会话标识)
            桥=getattr(pywebbridge,'window',None)
            桥=None if 桥 is None else getattr(桥,'__DSH_HOST_PATHS__',None)
            def 加文件(文件列,目录=None):
                '图片进草稿，有宿主路径的文件写成引用'
                if 目录 is None:
                    目录=set()
                if 会话面.binding(会话标识) is None:
                    return 中文['file.sessionUnavailable']
                快照=壳.snapshot
                if 快照['phase']=='adjudicating' or 快照['phase']=='submitting':
                    return 中文['attachment.dropBlocked']
                上传=[]
                引用=[]
                摘要=会话面.list.getSnapshot()['byId'].get(会话标识)
                工作目录=None if 摘要 is None else 摘要.get('cwd')
                for 文件 in 文件列:
                    是目录=文件 in 目录
                    if 桥 is None and 是目录:
                        return 中文['attachment.directoryDesktopOnly']
                    路径=''
                    if 桥 is not None:
                        路径=桥.pathFor(文件)
                    if 是目录 and 路径=='':
                        return 中文['attachment.pathUnavailable']
                    if 路径=='' or ((not 是目录) and 是图片媒体类型(文件.type)):
                        上传.append(文件)
                        continue
                    相对=相对化到工作目录(路径,工作目录)
                    提及=格式化文件提及({'path':相对+'/' if 是目录 else 相对,'kind':'file'},False)
                    if 提及 is None:
                        return 中文['attachment.pathUnsupported']
                    标签=工作区标题自(路径) or 文件.name
                    引用.append({
                        'source':'reference',
                        'ref':提及,
                        'label':标签+'/' if 是目录 else 标签,
                        'appearance':'folder' if 是目录 else 'file',
                        'clipboardText':提及,
                    })
                try:
                    草稿列=控制器.createDrafts(会话标识,上传)
                    标识列=[项['id'] for 项 in 草稿列]
                    if not 壳.addFiles(引用,标识列):
                        控制器.releaseDraftAttachments(草稿列)
                        return 中文['attachment.dropBlocked']
                    return None
                except 不支持图片媒体类型:
                    return 中文['image.unsupportedType']
                except Exception as 错误:
                    return str(错误)
            def 摘附件(标识):
                '壳收下之后再释放草稿'
                if 壳.removeAttachment(标识):
                    控制器.releaseDraftAttachment(标识)
            def 重试(标识):
                '绑定还在才重试上传'
                if 会话面.binding(会话标识) is not None:
                    控制器.retryFileUpload(会话标识,标识)
            def 切菜单(选区):
                '先关弹层再切换 command 源'
                壳.dismissPopup()
                快照=壳.snapshot
                壳前=快照['draft'][:选区['start']].strip()
                触发.toggleSource('command',{
                    'trigger':'/',
                    'query':'',
                    'quoted':False,
                    'position':'leading' if 壳前=='' else 'inline',
                    'span':{**选区,'draftRev':快照['draftRev']},
                })
            启动器=触发.launcher if 触发 is not None else None
            return {
                'keyboard':壳,
                'addFiles':加文件,
                'removeAttachment':摘附件,
                'resolveDraftAttachments':lambda 标识列:控制器.resolveDraftAttachments(标识列),
                'retryFileUpload':重试,
                'toggleCommandMenu':None if 触发 is None else 切菜单,
                'stop':lambda: 停止(会话标识),
                'hooks':{
                    'stopShortcut':停止快捷存储,
                    'busyEnter':提交.忙碌回车,
                    'fileUploads':控制器.fileUploads,
                    'notices':壳.notices,
                    'lexicon':壳.lexicon,
                    'menuLauncher':启动器 if 启动器 is not None else 缺席菜单,
                },
            }
        return 槽.register({
            'name':'conversation.composer.bar',
            'locale':命名空间,
            'children':{
                'conversation.input.attachments':{'kind':'single','scope':'session-maybe'},
                'conversation.input.overlay':{'kind':'list','scope':'session'},
                'conversation.input.permission':{'kind':'single','scope':'session'},
                'conversation.input.left':{'kind':'list','scope':'session'},
                'conversation.input.plan':{'kind':'single','scope':'session'},
                'conversation.input.right':{'kind':'list','scope':'session'},
                'conversation.input.model':{'kind':'single','scope':'session'},
                'conversation.input.activity':{'kind':'single','scope':'session'},
                'conversation.composer.dock':{'kind':'list','scope':'session'},
            },
            'inject':注入,
        },输入栏)
    def 挂主():
        'main 洞就绪后按序登记面板和子槽'
        yield 槽.register({
            'name':'main',
            'key':'conversation',
            'children':{'main.conversation':{'kind':'single','scope':'session-maybe'}},
        },会话面板)
        yield 登记根()
        yield 登记体()
        yield 登记会话()
        yield 登记页眉()
        yield 登记会话页眉()
        yield 登记栏()
    槽.inject('main',挂主)
    上下文.plugin(会话控制器,{
        'input':枢纽,
        'blocks':阻断表,
        'maxConcurrentFileUploads':并发,
    })
    上下文.plugin(待办停靠条目)
    上下文.plugin(队列停靠条目)

inject=依赖
apply=应用
