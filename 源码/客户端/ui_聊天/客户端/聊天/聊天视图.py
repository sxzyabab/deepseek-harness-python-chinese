from urllib.parse import quote
from ....ui_基础界面组件.icons import 图标下箭头描边常规
from ....ui_基础界面组件.markdown.Markdown委托 import Markdown委托提供方
from ....ui_基础界面组件.按钮 import 按钮
from ....ui_基础界面组件.模态 import 模态
from ....ui_对话.异常 import 标样式模块
from .....工具.工作区路径 import 是否绝对工作区路径,解析工作区路径
from ..约定.组树 import 在该层或更外
from .回合导航器 import 回合导航器
from .回合轨条目 import 合并回合轨条目
from .用披露 import 注入聊天样式,空属性
from .用聊天滚动 import 聊天滚动

__all__=['聊天视图']

样式模块='chat-view'
动效尾毫秒=800


def 打开失败文案(错误,回退):
    '宿主拒绝打开文件时用它的消息。空消息用回退文案'
    消息=getattr(错误,'message',None)
    if not isinstance(消息,str) or 消息=='':
        消息=str(错误)
    if 消息=='':
        return 回退
    return 消息


def 文件媒体(基址,路径):
    '绝对路径走文件接口'
    if (not str(基址).startswith('http:') and not str(基址).startswith('https:') and not str(基址).startswith('dsh-app://app/')):
        return None
    if not 是否绝对工作区路径(路径):
        return None
    if 路径.startswith('//') or 路径.startswith('\\\\'):
        return None
    return str(基址).rstrip('/')+'/api/file?path='+quote(路径,safe='')


def 观察到的输入(顺序,节点表):
    '已经落进转录的 rpc，以及最后一条输入所在回合'
    见到=set()
    最后回合=None
    for 键 in 顺序 or []:
        节点=节点表.get(键) if hasattr(节点表,'get') else None
        if not isinstance(节点,dict) or not 在该层或更外(节点,'input'):
            continue
        位置=节点.get('location') if isinstance(节点.get('location'),dict) else {}
        if 位置.get('kind') in ('turn','step') and isinstance(位置.get('turn'),dict):
            最后回合=位置['turn'].get('turn')
        数据=节点.get('data')
        来源=数据.get('source') if isinstance(数据,dict) else None
        if isinstance(来源,dict) and 来源.get('kind')=='user' and isinstance(来源.get('rpcId'),str):
            见到.add(来源['rpcId'])
    return {'rpcIds':见到,'lastInputTurn':最后回合}


class 聊天视图:
    '聊天槽。每一行交给带键的渲染席'
    def __init__(自身,属性=None):
        '记下视图属性并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.滚动=None
        自身.动效尾=False
        自身.动效定时=None
        自身.打开错误=None
        自身.打开忙=False
        自身.打开序号=0
        自身.导航=None
        自身.渲染中=False
        自身.待重画=False
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '创建帧时钟，并在折叠期间写上 data-chat-motion'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'聊天视图.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        if 自身.滚动 is None:
            自身.滚动=聊天滚动(窗口)
            自身.滚动.重画=自身.排队重画
        if 自身.渲染中:
            return 自身.根
        自身.渲染中=True
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='frame'
            标样式模块(自身.根,样式模块)
            自身.内=文档.createElement('div')
            自身.内.className='root'
            标样式模块(自身.内,样式模块)
            自身.滚盒=文档.createElement('div')
            自身.滚盒.className='scroll'
            标样式模块(自身.滚盒,样式模块)
            自身.列=文档.createElement('div')
            自身.列.className='column'
            标样式模块(自身.列,样式模块)
            自身.列.setAttribute('data-chat-flow','')
            自身.垫=文档.createElement('div')
            自身.垫.className='turnSpacer'
            标样式模块(自身.垫,样式模块)
            自身.垫.setAttribute('data-chat-turn-spacer','')
            自身.垫.setAttribute('aria-hidden','true')
            自身.滚盒.appendChild(自身.列)
            自身.滚盒.appendChild(自身.垫)
            自身.内.appendChild(自身.滚盒)
            自身.根.appendChild(自身.内)
            自身.底槽=文档.createElement('div')
            自身.底槽.className='toBottomSlot'
            标样式模块(自身.底槽,样式模块)
            自身.根.appendChild(自身.底槽)
        取聊天=属性.get('useChat')
        顺序=[]
        节点表=None
        导航项=[]
        if callable(取聊天):
            def 选顺序(快照):
                '可见顺序'
                return 快照.get('order') if isinstance(快照,dict) else []

            def 选节点(快照):
                '节点存储'
                return 快照.get('nodes') if isinstance(快照,dict) else None

            def 选导航(快照):
                '已加载回合'
                if not isinstance(快照,dict):
                    return []
                导航=快照.get('navigation')
                if hasattr(导航,'items'):
                    return 导航.items() or []
                return []

            顺序=取聊天(选顺序) or []
            节点表=取聊天(选节点)
            导航项=取聊天(选导航) or []
        分组=None
        if callable(属性.get('useConversation')):
            def 选分组(快照):
                '会话视图里的聊天分组'
                if not isinstance(快照,dict):
                    return None
                视图=快照.get('views')
                if hasattr(视图,'grouped'):
                    组=视图.grouped('chat')
                    if isinstance(组,dict):
                        return 组.get('entries')
                return None
            分组=属性['useConversation'](选分组)
        if 分组 is None:
            条目=[{'kind':'node','key':键} for 键 in 顺序]
        else:
            条目=分组
        呈现=属性.get('usePresentation')
        推迟完成=False
        转录模式=None
        if callable(呈现):
            def 选推迟(政策):
                '下一输入才折叠'
                return isinstance(政策,dict) and 政策.get('collapseTiming')=='next-input'

            def 选模式(政策):
                '转录模式'
                return None if not isinstance(政策,dict) else 政策.get('mode')

            推迟完成=呈现(选推迟) is True
            转录模式=呈现(选模式)
        大纲=None
        收件=None
        if callable(属性.get('useProjection')):
            大纲=属性['useProjection']('turnOutline')
            收件=属性['useProjection']('inbox')
        轨=合并回合轨条目(导航项,大纲)
        工作目录=None
        if callable(属性.get('useSessions')):
            def 选目录(快照):
                '会话列表上的工作目录'
                if not isinstance(快照,dict):
                    return None
                行=快照.get('byId')
                if isinstance(行,dict):
                    会话=行.get(属性.get('sessionId'))
                    if isinstance(会话,dict):
                        return 会话.get('cwd')
                return None
            工作目录=属性['useSessions'](选目录)
        在跑=False
        打开态=None
        打开错=None
        还有=False
        正加载=False
        待提交=[]
        if callable(属性.get('useSession')):
            def 选跑(快照):
                '会话是否还在跑'
                return isinstance(快照,dict) and 快照.get('running') is True

            def 选打开(快照):
                '打开状态'
                return None if not isinstance(快照,dict) else 快照.get('openState')

            def 选错(快照):
                '打开错误'
                return None if not isinstance(快照,dict) else 快照.get('openError')

            def 选还有(快照):
                '还有更早历史'
                return isinstance(快照,dict) and 快照.get('hasMore') is True

            def 选加载(快照):
                '正在加载更早'
                return isinstance(快照,dict) and 快照.get('loadingOlder') is True

            def 选待定(快照):
                '本地还没落盘的提交'
                if isinstance(快照,dict) and isinstance(快照.get('pendingSubmissions'),list):
                    return 快照['pendingSubmissions']
                return []

            在跑=属性['useSession'](选跑) is True
            打开态=属性['useSession'](选打开)
            打开错=属性['useSession'](选错)
            还有=属性['useSession'](选还有) is True
            正加载=属性['useSession'](选加载) is True
            待提交=属性['useSession'](选待定) or []
        自身.安排动效尾(窗口,推迟完成,在跑)
        插话=[]
        if isinstance(收件,dict) and isinstance(收件.get('next-step'),list):
            for 消息 in 收件['next-step']:
                if isinstance(消息,dict) and isinstance(消息.get('source'),dict) and 消息['source'].get('kind')=='user':
                    插话.append(消息)
        观察=观察到的输入(顺序,节点表 if 节点表 is not None else {})
        可见提交=[]
        if len(待提交)>0:
            for 提交 in 待提交:
                if isinstance(提交,dict) and 提交.get('placement')!='queued' and 提交.get('requestId') not in 观察['rpcIds']:
                    可见提交.append(提交)
        本地=dict((提交.get('requestId'),提交) for 提交 in 可见提交 if isinstance(提交,dict))
        本地号=set(提交.get('requestId') for 提交 in 待提交 if isinstance(提交,dict) and 提交.get('placement')!='queued')
        待定输入=[]
        for 项 in 插话:
            来源=项.get('source') if isinstance(项,dict) else None
            if not isinstance(来源,dict) or 来源.get('kind')!='user' or 'rpcId' not in 来源:
                待定输入.append(项)
                continue
            提交=本地.get(来源.get('rpcId'))
            if 提交 is None:
                if 来源.get('rpcId') not in 本地号:
                    待定输入.append(项)
            else:
                本地.pop(来源.get('rpcId'),None)
                待定输入.append(提交)
        for 提交 in 本地.values():
            待定输入.append(提交)
        推迟收=推迟完成 and not any(isinstance(项,dict) and 'requestId' in 项 and 项.get('placement')=='transcript' for 项 in 待定输入)
        首键=顺序[0] if len(顺序)>0 else None
        首序=None
        if 首键 is not None and hasattr(节点表,'get'):
            首节点=节点表.get(首键)
            if isinstance(首节点,dict):
                首序=首节点.get('anchorSeq')
        尾键=顺序[-1] if len(顺序)>0 else None
        尾是用户=False
        if 尾键 is not None and hasattr(节点表,'get'):
            尾节点=节点表.get(尾键)
            尾是用户=isinstance(尾节点,dict) and 尾节点.get('kind')=='user'
        最新插话=None
        下标=len(待定输入)-1
        while 下标>=0:
            if isinstance(待定输入[下标],dict) and 'source' in 待定输入[下标]:
                最新插话=待定输入[下标]
                break
            下标-=1
        插话号=None
        if isinstance(最新插话,dict):
            来源=最新插话.get('source') if isinstance(最新插话.get('source'),dict) else {}
            if 来源.get('kind')=='user' and 'rpcId' in 来源:
                插话号=来源.get('rpcId')
            else:
                插话号=最新插话.get('id')
        提交号=可见提交[-1].get('requestId') if len(可见提交)>0 and isinstance(可见提交[-1],dict) else None
        while 自身.列.firstChild is not None:
            自身.列.removeChild(自身.列.firstChild)
        if 打开态=='loading':
            提示=文档.createElement('div')
            提示.className='hint'
            标样式模块(提示,样式模块)
            提示.textContent=翻译('chat.loadingHistory')
            自身.列.appendChild(提示)
        if 打开态=='error' and isinstance(打开错,dict):
            错=文档.createElement('div')
            错.className='openError'
            标样式模块(错,样式模块)
            错.textContent=翻译('chat.loadError',{'message':打开错.get('message'),'code':打开错.get('code')})
            自身.列.appendChild(错)
        if 还有:
            更早=文档.createElement('div')
            更早.className='older'
            标样式模块(更早,样式模块)
            钮=文档.createElement('button')
            钮.type='button'
            钮.disabled=正加载
            钮.textContent=翻译('loading') if 正加载 else 翻译('chat.loadOlder')

            def 加载(事件=None):
                '再要一页更早的历史'
                自身.滚动.加载更早()

            钮.addEventListener('click',加载)
            更早.appendChild(钮)
            自身.列.appendChild(更早)
        动效开=推迟完成 and 自身.滚动.已开 and (在跑 or 自身.动效尾 or len(待定输入)>0)
        空属性(自身.列,'data-chat-motion',动效开)
        基址=''
        try:
            基址=文档.baseURI or ''
        except Exception:
            基址=''

        def 解析图(路径):
            '相对工作目录的图片'
            return 文件媒体(基址,解析工作区路径(工作目录,路径))

        委托=Markdown委托提供方({
            'openFile':自身.请求打开,
            'openExternalLink':属性.get('openExternalLink'),
            'fileImages':{
                'resolve':解析图,
                'labels':{
                    'open':翻译('image.open'),
                    'loading':翻译('image.loading'),
                    'failed':翻译('image.failed'),
                    'dialog':翻译('image.dialog'),
                    'close':翻译('image.close'),
                },
            },
        })
        委托.渲染()
        槽=属性.get('renderSlot')
        if callable(槽):
            流=槽('conversation.chat.flow',{
                'window':窗口,
                'entries':条目,
                'pendingInputs':待定输入,
                'lastInputTurn':观察['lastInputTurn'],
                'deferCollapse':推迟收,
                'cwd':工作目录,
                'openFile':自身.请求打开,
                'inspectCall':属性.get('inspectCall'),
                'forkAt':属性.get('forkAt'),
                'loadImage':属性.get('loadImage'),
                'fileMentions':属性.get('fileMentions'),
                'parent':自身.列,
            },{'hookContext':{'motion':自身.滚动.视口.动效},'window':窗口})
            if 流 is not None and hasattr(流,'tagName') and 流.parentNode is None:
                自身.列.appendChild(流)
        委托.拆除()
        空属性(自身.内,'data-chat-following-tail',自身.滚动.状态.get('followingTail') is True)
        while 自身.底槽.firstChild is not None:
            自身.底槽.removeChild(自身.底槽.firstChild)
        if not 自身.滚动.状态.get('followingTail'):
            到底=文档.createElement('button')
            到底.type='button'
            到底.className='toBottom'
            标样式模块(到底,样式模块)
            到底.setAttribute('aria-label',翻译('chat.toBottom'))
            箭头=图标下箭头描边常规({'window':窗口})
            if 箭头 is not None:
                到底.appendChild(箭头)

            def 回底(事件=None):
                '回到转录底部'
                自身.滚动.回到底()
                自身.渲染()

            到底.addEventListener('click',回底)
            自身.底槽.appendChild(到底)
        if 自身.导航 is not None and 自身.导航.根 is not None and 自身.导航.根.parentNode is 自身.根:
            自身.导航.根.remove()
        if 自身.滚动.状态.get('initialized'):
            自身.导航=回合导航器({
                'window':窗口,
                'items':轨,
                'activeTurn':自身.滚动.状态.get('activeTurn'),
                'busyTurn':自身.滚动.忙回合值,
                'onNavigate':自身.滚动.导航到回合,
                't':翻译,
                'parent':自身.根,
            })
        if 自身.打开错误 is not None:
            自身.画打开错误(文档,窗口,翻译)
        自身.滚动.提交({
            'ready':打开态=='open',
            'order':顺序,
            'firstSeq':首序,
            'lastKey':尾键,
            'lastIsUser':尾是用户,
            'steeringId':插话号,
            'submissionId':提交号,
            'running':在跑,
            'deferCompletedTurns':推迟完成,
            'transcriptView':转录模式,
            'loadedTurns':导航项,
            'chatScroll':属性.get('chatScroll'),
            'hasMore':还有,
            'loadingOlder':正加载,
            'loadOlder':属性.get('loadOlder'),
            'loadThrough':属性.get('loadThrough'),
            'list':自身.滚盒,
            'column':自身.列,
        })
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        自身.渲染中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 排队重画(自身):
        '阅读状态在这次绘制里变了，画完再画一次'
        if 自身.渲染中:
            自身.待重画=True
        else:
            自身.渲染()

    def 安排动效尾(自身,窗口,推迟,在跑):
        '回合停了之后，折叠动效再留一小段'
        if not 推迟:
            自身.动效尾=False
            return
        if 在跑:
            自身.动效尾=True
            return
        if 自身.动效尾 and 自身.动效定时 is None and hasattr(窗口,'setTimeout'):
            def 停():
                '尾声结束'
                自身.动效定时=None
                自身.动效尾=False
                自身.渲染()
            自身.动效定时=窗口.setTimeout(停,动效尾毫秒)

    def 请求打开(自身,路径,选项=None):
        '打开失败就留在页内对话框里'
        自身.打开序号+=1
        序号=自身.打开序号
        自身.打开忙=True
        打开=自身.属性.get('openFile')
        try:
            if 选项 is None:
                打开(路径)
            else:
                打开(路径,选项)
        except Exception as 错误:
            if 序号!=自身.打开序号:
                return
            译=自身.属性.get('t')
            回退=译('fileOpen.unknown') if callable(译) else 'fileOpen.unknown'
            自身.打开错误={'path':路径,'message':打开失败文案(错误,回退)}
            自身.打开忙=False
            自身.渲染()
            return
        if 序号!=自身.打开序号:
            return
        自身.打开错误=None
        自身.打开忙=False

    def 关掉打开错误(自身):
        '忽略还在飞的那一次'
        自身.打开序号+=1
        自身.打开错误=None
        自身.打开忙=False
        自身.渲染()

    def 画打开错误(自身,文档,窗口,翻译):
        '打开文件被拒绝时的对话框'
        关=按钮({'window':窗口,'variant':'outline','className':'modalAction','children':翻译('cancel'),'onClick':自身.关掉打开错误})
        def 重试(事件=None):
            '再打开同一路径'
            if 自身.打开错误 is not None:
                自身.请求打开(自身.打开错误['path'])
        再=按钮({'window':窗口,'variant':'primary','className':'modalAction','disabled':自身.打开忙,'children':翻译('retry'),'onClick':重试})
        框=模态({
            'window':窗口,
            'open':True,
            'onClose':自身.关掉打开错误,
            'closeLabel':翻译('close'),
            'title':翻译('fileOpen.title'),
            'description':自身.打开错误.get('message'),
            'footer':[关,再],
            'parent':自身.根,
        })
        框.渲染()
