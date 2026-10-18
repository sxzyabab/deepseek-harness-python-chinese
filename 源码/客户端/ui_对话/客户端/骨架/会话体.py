from ...异常 import 标样式模块,挂上,是页面节点
from .空主视觉 import 工作区标签,工作区芯片,英雄壳

__all__=['会话体','无宽度控件']

样式模块='conversation-root'
默认工作区目录='default-workspace'

class 无宽度控件:
    '没有登记宽度控件时的空工厂'
    def __init__(自身,属性):
        '不画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '没有节点'
        return None

class 会话视图席:
    '工厂缺省时画出 conversation.session'
    def __init__(自身,属性):
        '记下绘制函数'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '把会话槽放进不占布局的壳'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        壳=文档.createElement('div')
        壳.style.display='contents'
        挂上(壳,属性['renderSlot']('conversation.session',{'window':窗口}))
        自身.根=壳
        return 壳

class 会话体:
    '共享会话体：视图、撰写器链、英雄和工作区芯片'
    def __init__(自身,属性):
        '记下选择和待定工作区'
        自身.属性=属性
        自身.根=None
        自身.选择器开=False
        自身.待定工作区=None
        自身.锚=None
        自身.座位观察=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 渲染(自身):
        '英雄居中，活动阶段停靠。无工作区时输入栏是选择器触发器'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            会话标识=属性.get('sessionId')
            会话=属性['useSession'](lambda 快照:快照)
            列表=属性['useSessions'](lambda 快照:快照)
            工作区=属性['useWorkspaces'](lambda 快照:快照)
            输入态=属性['useInput'](lambda 快照:快照)
            def 读待定(快照):
                '当前会话的待定交互'
                if 会话标识 is None:
                    return None
                项=快照.get(会话标识) if hasattr(快照,'get') else None
                if 项 is None:
                    return None
                return 项.get('pendingInteraction')
            待定交互=属性['useSessionStatus'](读待定)
            工作目录=None
            if 会话标识 is not None and isinstance(列表,dict):
                摘要=列表.get('byId',{}).get(会话标识)
                if isinstance(摘要,dict):
                    工作目录=摘要.get('cwd')
            阻断=属性['useComposerBlock'](lambda 块:块)
            会话工作区=None
            if 会话标识 is not None and isinstance(工作区,dict):
                for 项 in 工作区.get('items') or []:
                    if 会话标识 in (项.get('sessionIds') or []):
                        会话工作区=项
                        break
            待定项=None
            if 自身.待定工作区 is not None and isinstance(工作区,dict):
                for 项 in 工作区.get('items') or []:
                    if 项.get('workspaceId')==自身.待定工作区:
                        待定项=项
                        break
            if 自身.待定工作区 is not None:
                if (会话工作区 is not None and 会话工作区.get('workspaceId')==自身.待定工作区) or (工作区.get('phase')=='ready' and 待定项 is None):
                    自身.待定工作区=None
                    待定项=None
            存下标题=None
            if 待定项 is not None:
                存下标题=待定项.get('title')
            elif 会话标识 is None:
                存下标题=None
            elif 会话工作区 is not None:
                存下标题=会话工作区.get('title')
            elif 工作区.get('phase')=='ready' or 工作目录 is None or 工作目录=='':
                存下标题=None
            else:
                存下标题=工作区标签(工作目录)
            if 存下标题 is None:
                芯片标题=None
            elif 存下标题==默认工作区目录:
                芯片标题='默认工作区'
            else:
                芯片标题=存下标题
            惰性=会话标识 is None or (属性.get('hero') is True and 芯片标题 is None)
            被挡=(not 惰性) and 阻断 is not None
            父=None
            if 自身.根 is not None:
                父=自身.根.parentNode
                自身.根.remove()
            elif 'parent' in 属性:
                父=属性['parent']
            if 自身.座位观察 is not None:
                自身.座位观察.disconnect()
                自身.座位观察=None
            体=文档.createElement('div')
            类名='body'
            if 属性.get('variant')=='embedded':
                类名=类名+' embeddedBody'
            体.className=类名
            标样式模块(体,样式模块)
            体.setAttribute('data-conversation-content','')
            if 会话标识 is not None:
                体.setAttribute('data-conversation-session',str(会话标识))
            体.setAttribute('data-conversation-region','chat')
            体.setAttribute('data-content-phase','' if 属性.get('phase') is None else str(属性['phase']))
            滚动=文档.createElement('div')
            滚动.className='scrollBody'
            标样式模块(滚动,样式模块)
            滚动.setAttribute('data-conversation-scroll','')
            if 会话标识 is not None:
                视图类=None
                钩=属性.get('useFactorySlot')
                if 钩 is not None:
                    try:
                        视图类=钩('views',会话视图席)
                    except Exception as 出厂:
                        del 出厂
                if 视图类 is None:
                    视图=会话视图席({'renderSlot':属性['renderSlot'],'window':窗口})
                else:
                    视图=视图类({'window':窗口})
                if 视图.根 is not None:
                    滚动.appendChild(视图.根)
            栈类='composerStack'
            if 属性.get('hero') is True:
                栈类=栈类+' composerHero'
            栈=文档.createElement('div')
            栈.className=栈类
            标样式模块(栈,样式模块)
            if 属性.get('hero') is True:
                壳=英雄壳({'renderSlot':属性['renderSlot'],'window':窗口})
                if 壳.根 is not None:
                    栈.appendChild(壳.根)
                行=文档.createElement('div')
                行.className='heroWorkspaceRow'
                标样式模块(行,样式模块)
                自身.锚={'current':None}
                芯片=工作区芯片({
                    'buttonRef':自身.锚,
                    'label':芯片标题,
                    'menuOpen':自身.选择器开,
                    'window':窗口,
                    'onClick':自身.切换选择器,
                })
                行.appendChild(芯片.根)
                选中=自身.待定工作区 if 自身.待定工作区 is not None else (None if 会话工作区 is None else 会话工作区.get('workspaceId'))
                挂上(行,属性['renderSlot']('conversation.hero.workspace',{
                    'open':自身.选择器开,
                    'anchorRef':自身.锚,
                    'selectedId':选中,
                    'onPick':自身.挑选,
                    'onClose':自身.关闭选择器,
                    'window':窗口,
                }))
                挂上(行,属性['renderSlot']('conversation.hero.agentPreset',{'window':窗口}))
                if 会话标识 is not None:
                    选项=文档.createElement('div')
                    选项.className='heroOptions'
                    标样式模块(选项,样式模块)
                    挂上(选项,属性['renderSlot']('conversation.hero.options',{'window':窗口}))
                    行.appendChild(选项)
                栈.appendChild(行)
            if 会话 is not None and 输入态 is not None:
                挂上(栈,属性['renderSlot']('conversation.input.dock',{
                    'session':会话,
                    'input':输入态,
                    'window':窗口,
                }))
            栏主={'variant':'hero' if 属性.get('hero') is True else 'composer','window':窗口}
            if 惰性:
                栏主['placeholder']='描述你想要构建的内容, / 调用指令, @ 文件或对话'
                栏主['workspacePickerOpen']=自身.选择器开
                栏主['onRequestWorkspace']=自身.打开选择器
            elif 被挡:
                栏主['blocked']=阻断
                栏主['placeholder']=阻断.get('reason') if isinstance(阻断,dict) else ''
            elif 属性.get('hero') is True:
                栏主['placeholder']='描述你想要构建的内容, / 调用指令, @ 文件或对话'
            栏=属性['renderSlot']('conversation.composer.bar',栏主)
            挂上(栈,栏)
            座位=文档.createElement('div')
            座位.className='composerSeat'
            标样式模块(座位,样式模块)
            座位.setAttribute('data-composer-seat','')
            座位.setAttribute('data-conversation-region','composer')
            链主={'sessionId':会话标识,'session':会话,'pendingInteraction':待定交互,'window':窗口}
            链=属性['renderSlotChain']('conversation.composer',链主,{
                'fallback':栈,
                'fallbackOnly':会话标识 is None,
                'overlay':True,
            })
            挂上(座位,链)
            滚动.appendChild(座位)
            体.appendChild(滚动)
            宽度类=无宽度控件
            宽度钩=属性.get('useFactorySlot')
            if 宽度钩 is not None:
                try:
                    宽度类=宽度钩('widthControls',无宽度控件)
                except Exception as 出厂:
                    del 出厂
            宽度=宽度类({'container':体,'phase':属性.get('phase'),'window':窗口})
            try:
                宽度根=object.__getattribute__(宽度,'根')
            except AttributeError:
                宽度根=None
            if 是页面节点(宽度根):
                体.appendChild(宽度根)
            自身.根=体
            if 父 is not None:
                父.appendChild(自身.根)
            if not 自身.已订:
                def 变更():
                    '会话、工作区或输入变了就重画'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    自身.渲染()
                for 名 in ('useSession','useSessions','useWorkspaces','useInput','useSessionStatus','useComposerBlock'):
                    钩=属性.get(名)
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):
                        自身.退订.append(钩._subscribe(变更))
                自身.已订=True
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 切换选择器(自身):
        '打开或关上工作区菜单后重画'
        自身.选择器开=not 自身.选择器开
        自身.渲染()

    def 打开选择器(自身):
        '无工作区时从输入栏请求打开'
        自身.选择器开=True
        自身.渲染()

    def 关闭选择器(自身):
        '菜单自己关上'
        自身.选择器开=False
        自身.渲染()

    def 挑选(自身,工作区标识):
        '先记下待定工作区，再交给 selectWorkspace。失败且仍是这一项就清掉'
        自身.选择器开=False
        自身.待定工作区=工作区标识
        try:
            结果=自身.属性['selectWorkspace'](工作区标识)
            if hasattr(结果,'等待'):
                结果.等待()
        except Exception:
            if 自身.待定工作区==工作区标识:
                自身.待定工作区=None
        自身.渲染()
