import os
from ...异常 import 注入模块样式文件,标样式模块,挂上,接上
from ..视图选中项 import 解析活动视图
from .默认视图 import 默认会话视图

__all__=['会话页眉','会话']

样式模块='conversation-root'

def 面包屑相同(左,右):
    '两条面包屑的标识和显示标题都相同。交给 useSessions 做相等比较，不收进调用处'
    if len(左)!=len(右):
        return False
    下标=0
    while 下标<len(左):
        甲=左[下标]
        乙=右[下标]
        if 乙 is None or 甲['id']!=乙['id'] or 甲['displayTitle']!=乙['displayTitle']:
            return False
        下标+=1
    return True

def 确保样式(文档):
    '会话根样式只插一次。页眉和会话体共用这一份'
    注入模块样式文件(
        文档,
        '会话根样式',
        os.path.join(os.path.dirname(__file__),'会话根.module.css'),
        样式模块,
    )

def 标(节点,类名):
    '官方类名留在元素上，再用样式模块接上选择器'
    节点.className=类名
    return 标样式模块(节点,样式模块)

class 会话页眉:
    '会话开始后画出标题、谱系、动作、工具、角标和视图页签'
    def __init__(自身,属性):
        '记下渲染器交来的 props，并画出这一条页眉'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 渲染(自身):
        '面包屑里，当前项和子智能体项把 conversation.session.header.lineage 画进这一段'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            属性=自身.属性
            窗口=属性['window']
            文档=窗口.document
            确保样式(文档)
            页签列=属性['useConversationViews'](lambda 值:值)
            选中标识=属性['useStore'](lambda 快照:快照['view'])
            活动=解析活动视图(页签列,选中标识)
            会话标识=属性['sessionId']
            def 选择祖先(列表):
                '从当前会话沿父级收成面包屑，环和断链都停'
                链=[]
                见过=set()
                游标=会话标识
                while 游标 is not None:
                    if 游标 in 见过:
                        break
                    见过.add(游标)
                    摘要=列表['byId'][游标] if 游标 in 列表['byId'] else None
                    if 摘要 is None:
                        break
                    链.insert(0,{
                        'id':摘要['id'],
                        'displayTitle':摘要.get('displayTitle') or 摘要.get('title') or '',
                        'subagent':摘要.get('origin')=='subagent',
                    })
                    if 摘要.get('origin')!='subagent':
                        break
                    游标=摘要.get('parentId')
                return 链
            祖先=属性['useSessions'](选择祖先,面包屑相同)
            藏铬=属性.get('hideChrome') is True
            显示页签=(not 藏铬) and len(页签列)>1
            旧=自身.根
            父=旧.parentNode if 旧 is not None else (属性['parent'] if 'parent' in 属性 else None)
            壳=文档.createElement('div')
            壳.style.display='contents'
            标题行=标(文档.createElement('div'),'titleRow')
            if not 藏铬:
                簇=标(文档.createElement('div'),'titleCluster')
                导航=标(文档.createElement('nav'),'crumbs')
                导航.setAttribute('aria-label','会话层级')
                for 序号,摘要 in enumerate(祖先):
                    最后=序号==len(祖先)-1
                    段=标(文档.createElement('span'),'crumbSeg')
                    if 序号>0:
                        分隔=标(文档.createElement('span'),'crumbSep')
                        分隔.textContent='/'
                        段.appendChild(分隔)
                    类名='crumb'
                    if 摘要['subagent']:
                        类名=类名+' crumbSubagent'
                    if 最后:
                        类名=类名+' crumbCurrent'
                        标题=标(文档.createElement('span'),类名)
                    else:
                        标题=标(文档.createElement('button'),类名)
                        标题.type='button'
                        标识=摘要['id']
                        def 点开(事件,标识=标识):
                            '打开这条祖先会话'
                            属性['open'](标识)
                        标题.addEventListener('click',点开)
                    标题.textContent=摘要['displayTitle']
                    属主={
                        'lineageSessionId':摘要['id'],
                        'displayTitle':摘要['displayTitle'],
                        'window':窗口,
                    }
                    if not 最后:
                        标识=摘要['id']
                        def 打开标题(标识=标识):
                            '谱系槽请求打开这条标题'
                            属性['open'](标识)
                        属主['openTitle']=打开标题
                    if 最后 or 摘要['subagent']:
                        if 摘要['subagent']:
                            挂上(段,属性['renderSlot'](
                                'conversation.session.header.lineage',
                                属主,
                                {'fallback':标题},
                            ))
                        else:
                            段.appendChild(标题)
                            挂上(段,属性['renderSlot'](
                                'conversation.session.header.lineage',
                                属主,
                                {'fallback':None},
                            ))
                    else:
                        段.appendChild(标题)
                    导航.appendChild(段)
                if len(祖先)==0:
                    当前=标(文档.createElement('span'),'crumbCurrent')
                    当前.textContent='' if 会话标识 is None else str(会话标识)
                    导航.appendChild(当前)
                簇.appendChild(导航)
                动作=标(文档.createElement('div'),'headerActions')
                挂上(动作,属性['renderSlot']('conversation.session.header.actions',{'window':窗口}))
                簇.appendChild(动作)
                标题行.appendChild(簇)
                工具=标(文档.createElement('div'),'headerUtilities')
                挂上(工具,属性['renderSlot']('conversation.session.header.utilities',{'window':窗口}))
                标题行.appendChild(工具)
            角=标(文档.createElement('div'),'headerCorner')
            角.setAttribute('data-conversation-header-corner','')
            挂上(角,属性['renderSlot']('conversation.session.header.corner',{'window':窗口}))
            标题行.appendChild(角)
            壳.appendChild(标题行)
            if 显示页签:
                页=标(文档.createElement('div'),'tabs')
                页.setAttribute('role','tablist')
                页.setAttribute('data-conversation-tabs','')
                for 视图页 in 页签列:
                    选中=活动 is not None and 视图页['id']==活动['id']
                    钮=标(文档.createElement('button'),'tab tabActive' if 选中 else 'tab')
                    钮.type='button'
                    钮.setAttribute('role','tab')
                    钮.setAttribute('aria-selected','true' if 选中 else 'false')
                    钮.textContent=视图页['label']
                    标识=视图页['id']
                    def 选页(事件,标识=标识):
                        '切到这个已登记视图'
                        属性['selectView'](标识)
                    钮.addEventListener('click',选页)
                    页.appendChild(钮)
                壳.appendChild(页)
            自身.根=接上(旧,壳,父)
            if not 自身.已订:
                def 变更():
                    '会话列表、视图或选中项变了就重画'
                    if 自身.绘制中:
                        自身.待重画=True
                        return
                    if 自身.根 is None or 自身.根.parentNode is None:
                        return
                    自身.渲染()
                for 名 in ('useSessions','useConversationViews','useStore'):
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

class 会话:
    '滚动区里的活动视图。空白英雄阶段不画视图'
    def __init__(自身,属性):
        '把严格会话份额交给默认视图'
        自身.属性=属性
        自身.视图=默认会话视图(属性)
        自身.根=自身.视图.根

    def 渲染(自身):
        '重画内部的默认视图'
        自身.视图.属性=自身.属性
        自身.根=自身.视图.渲染()
        return 自身.根
