import importlib,os,uuid#按写死的模块路径装入插件，并读壳样式
import traceback#失败时把栈留在启动页
from ...依赖.cordis.上下文 import 上下文 as 上下文类#本进程的 Cordis
from ..模块.客户端.通告 import 登记握手窗口#页面窗口只用握手传进来的
from ..ui_渲染器.客户端.绑定 import 可观察源#空会话源
from .启动页 import 启动页#加载过程
from .挂载 import 挂载客户端#uiRenderer 挂进容器

#暂时写死的装配清单。官方 YAML 是同一类数据：id 定位这一行，模块是迁移后的包。
#文件顺序不决定挂载顺序，下面按依赖能不能满足来决定装不装。
名册=[
    {'id':'connection','依赖':[],'模块':'客户端.连接.客户端'},
    {'id':'typert','依赖':[],'模块':'类型化远程调用.注册表.客户端'},
    {'id':'api-gateway','依赖':['typert','connection'],'模块':'api.网关.客户端'},
    {'id':'ui-renderer','依赖':[],'模块':'客户端.ui_渲染器.客户端'},
    {'id':'locale','依赖':['slots','remote','configForms'],'模块':'客户端.本地化.客户端'},
    {'id':'ui-theme','依赖':['slots','locale','remote','configForms'],'模块':'客户端.ui_主题.客户端'},
    {'id':'shortcuts','依赖':['locale'],'模块':'客户端.快捷键.客户端'},
    {'id':'ui-layout','依赖':['slots','theme','locale','shortcuts'],'模块':'客户端.ui_布局.客户端'},
    {'id':'ui-session','依赖':['sessions','slots','remote','remoteAccess'],'模块':'客户端.ui_会话.客户端'},
    {'id':'ui-workspace','依赖':['slots','sessions','workspaces','locale','remote','remote.directoryPicker','layout','shortcuts','remoteAccess'],'模块':'客户端.ui_工作区.客户端'},
    {'id':'ui-sidebar','依赖':['slots','layout','uiWorkspace','locale','shortcuts'],'模块':'客户端.ui_侧边栏.客户端'},
    {'id':'ui-conversation','依赖':['slots','sessions','fileUpload','uiSession','uiWorkspace','locale','configForms'],'模块':'客户端.ui_对话.客户端'},
    {'id':'ui-chat','依赖':['slots','sessions','uiWorkspace','uiSession','uiConversation','locale','configForms','remote','remote.session','sidebarRight'],'模块':'客户端.ui_聊天.客户端'},
]#名册结束


class 空配置:
    '启动时写死的配置表单。值还没从宿主来，快照保持空'
    def getSnapshot(自身):
        '当前没有分区'
        return {'status':'ready','value':None,'base':None,'user':None,'revision':None,'writable':False}

    def subscribe(自身,监听):
        '没有后续更新'
        return lambda:None

    def set(自身,*位置参数):
        '启动数据不可写'
        return False

    def unset(自身,*位置参数):
        '启动数据不可写'
        return False

    def mutate(自身,*位置参数):
        '启动数据不可写'
        return False


class 开关源:
    '开发者工具开关。启动时关着'
    def getSnapshot(自身):
        '关'
        return False

    def subscribe(自身,监听):
        '不会变'
        return lambda:None


class 开发者工具:
    '对话页签要读 enabled'
    def __init__(自身):
        '关着'
        自身.enabled=开关源()


class 配置表单:
    '每个命名空间都先给同一份空快照'
    def __init__(自身):
        '开发者工具固定关'
        自身.developerTools=开发者工具()

    def get(自身,命名空间):
        'locale 和 theme 启动时要读的那份'
        return 空配置()

    def describe(自身):
        '还没有描述镜像'
        return 空配置()


class 空会话表:
    '根上的 sessions 钩子。还没有会话服务，列表保持空'
    def getSnapshot(自身):
        '没有会话'
        return {'byId':{},'ids':[]}

    def subscribe(自身,监听):
        '这份表不会变'
        return lambda:None


class 列表仓:
    '空会话列表。ui-session 按名字取 getSnapshot 和 subscribe'
    def __init__(自身):
        '还没有会话，基线已经就绪'
        自身.状态={'ids':[],'byId':{},'phase':'ready','projectionsBySession':{}}
        自身.监听=set()

    def getSnapshot(自身):
        '当前列表'
        return 自身.状态

    def subscribe(自身,监听):
        '登记。这份表启动后不写'
        自身.监听.add(监听)
        return lambda:自身.监听.discard(监听)

    def __getitem__(自身,键):
        '按 getSnapshot、subscribe 取方法'
        if 键=='getSnapshot':
            return 自身.getSnapshot
        if 键=='subscribe':
            return 自身.subscribe
        raise KeyError(键)

    def 通知(自身):
        '快照已经改过，叫订阅者重读'
        for 监听 in list(自身.监听):
            监听()


class 保留仓:
    '没有人持有这份会话'
    def getSnapshot(自身):
        '保留计数是空的'
        return {'retainedBy':{}}

    def subscribe(自身,监听):
        '不会变'
        return lambda:None

    def __getitem__(自身,键):
        '按名字取方法'
        if 键=='getSnapshot':
            return 自身.getSnapshot
        if 键=='subscribe':
            return 自身.subscribe
        raise KeyError(键)


class 本地作用域:
    '一份会话自己的副作用。对话和聊天往这里登记'
    def __init__(自身):
        '还没有拆除器'
        自身._拆=[]

    def effect(自身,函数,名称=None):
        '马上执行，留下拆除器'
        拆除=函数()
        if not callable(拆除):
            拆除=lambda:None
        自身._拆.append(拆除)
        return 拆除

    def 副作用(自身,函数,名称=None):
        '中文名和 effect 是同一个'
        return 自身.effect(函数,名称)

    def get(自身,名称):
        '这一域里还没有别的服务'
        return None


class 投影面:
    '会话投影。还没有宿主投影时读出来是空'
    def 面(自身,键):
        '任意键都给一份空源'
        def 读():
            '没有投影'
            return None
        def 订(监听):
            '不会变'
            return lambda:None
        return {'getSnapshot':读,'subscribe':订}


class 事件窗:
    '会话事件。空窗可以整窗替换，之后按一条一条追加'
    def __init__(自身):
        '从第 0 次修订开始'
        自身.修订=0
        自身.条目=[]
        自身.监听=set()
        自身.变更={'kind':'replace'}

    def getSnapshot(自身):
        '当前整窗'
        return {'revision':自身.修订,'entries':自身.条目,'hasMore':False,'change':自身.变更}

    def subscribe(自身,监听):
        '登记'
        自身.监听.add(监听)
        return lambda:自身.监听.discard(监听)

    def 追加(自身,记录):
        '尾部加一条，并告诉已经在听的人'
        自身.条目.append(记录)
        自身.修订=自身.修订+1
        自身.变更={'kind':'append','entries':[记录]}
        for 监听 in list(自身.监听):
            监听()


class 本地会话:
    '这一页上的一份会话。发送先留下用户这句话'
    def __init__(自身,标识,目录,事件,发布):
        '空白，等第一句'
        自身.sessionId=标识
        自身.目录=目录
        自身.事件=事件
        自身.发布=发布
        自身.projections=投影面()
        自身.序号=0
        自身.状态={
            'id':标识,
            'sessionId':标识,
            'blank':True,
            'awaitingFirstTurn':True,
            'running':False,
            'promptAttempted':False,
            'openState':'open',
            'removed':False,
            'cwd':目录,
        }
        自身.监听=set()

    def getSnapshot(自身):
        '界面读的会话状态'
        return 自身.状态

    def subscribe(自身,监听):
        '登记'
        自身.监听.add(监听)
        return lambda:自身.监听.discard(监听)

    def _通知(自身):
        '状态变了'
        for 监听 in list(自身.监听):
            监听()

    def beginSubmission(自身,选项):
        '发送前要一个请求号'
        return {'requestId':str(uuid.uuid4())}

    def prompt(自身,内容,方式,信号=None,请求号=None):
        '把文本留进事件窗，会话不再是空白'
        文本=''
        if isinstance(内容,list):
            for 项 in 内容:
                if isinstance(项,dict) and 项.get('type')=='text':
                    文本=项.get('text') or ''
        自身.序号=自身.序号+1
        自身.事件.追加({
            'event':{
                'seq':自身.序号,
                'type':'user/message',
                'time':None,
                'data':{
                    'id':str(uuid.uuid4()),
                    'content':{'text':文本,'attachments':[],'extraBlocks':[],'referenceLabels':[]},
                    'source':{'kind':'user'},
                },
            },
        })
        自身.状态['blank']=False
        自身.状态['awaitingFirstTurn']=False
        自身.状态['promptAttempted']=True
        自身._通知()
        自身.发布(文本)
        return {'ok':True}


class 本地绑定:
    'ui-session 和对话共用的这一代会话'
    def __init__(自身,标识,目录,发布):
        '会话、作用域、事件窗'
        自身.sessionId=标识
        自身.ctx=本地作用域()
        自身.eventSource=事件窗()
        自身.session=本地会话(标识,目录,自身.eventSource,发布)

    def __getitem__(自身,键):
        '内置解析按键取会话和标识'
        if 键=='session':
            return 自身.session
        if 键=='sessionId':
            return 自身.sessionId
        if 键=='ctx':
            return 自身.ctx
        raise KeyError(键)


class 保留引用:
    '主视图持有的一次保留'
    def __init__(自身,标识,放开):
        '记下标识和放开的动作'
        自身.sessionId=标识
        自身.release=放开


class 本地宿主:
    '这一页的工作区和会话。没有远端宿主时，新建和发送都落在这里'
    def __init__(自身):
        '两份列表都先就绪，里面还是空的'
        自身.会话列表=列表仓()
        自身.工作区列表=列表仓()
        路径=os.getcwd()
        自身.工作区列表.状态={
            'phase':'ready',
            'items':[{
                'workspaceId':'default',
                'path':路径,
                'title':os.path.basename(路径.rstrip('\\/')) or 路径,
                'sessionIds':[],
                'createdAt':'2026-01-01T00:00:00',
            }],
            'archivedSessionIds':[],
            'pinnedSessionIds':[],
        }
        自身.绑定={}
        自身.行={}

    def initializeDefault(自身,信号=None):
        '第一次需要工作时建一个默认工作区'
        if len(自身.工作区列表.状态['items'])>0:
            return {'workspaceId':自身.工作区列表.状态['items'][0]['workspaceId']}
        路径=os.getcwd()
        标识='default'
        自身.工作区列表.状态['items'].append({
            'workspaceId':标识,
            'path':路径,
            'title':os.path.basename(路径.rstrip('\\/')) or 路径,
            'sessionIds':[],
            'createdAt':'2026-01-01T00:00:00',
        })
        自身.工作区列表.通知()
        return {'workspaceId':标识}

    def _工作区(自身,标识):
        '按标识找工作区行'
        for 项 in 自身.工作区列表.状态['items']:
            if 项['workspaceId']==标识:
                return 项
        return None

    def create(自身,请求=None):
        '在工作区里建一份会话，或复用点名的那份'
        if 请求 is None:
            请求={}
        已有=请求.get('sessionId')
        if isinstance(已有,str) and 已有 in 自身.绑定:
            return 已有
        工作区号=请求.get('workspaceId')
        工作区=自身._工作区(工作区号)
        目录=工作区['path'] if 工作区 is not None else os.getcwd()
        标识=已有 if isinstance(已有,str) and 已有!='' else str(uuid.uuid4())
        def 发布(文本):
            '这句话写进列表标题'
            行=自身.行.get(标识)
            if 行 is None:
                return
            if 文本!='':
                行['title']=文本
                行['displayTitle']=文本
                行['blank']=False
            行['updatedAt']=行['updatedAt']+1
            自身.会话列表.通知()
        绑定=本地绑定(标识,目录,发布)
        自身.绑定[标识]=绑定
        自身.行[标识]={
            'id':标识,
            'blank':True,
            'cwd':目录,
            'running':False,
            'retainedBy':{},
            'title':'新会话',
            'displayTitle':'新会话',
            'updatedAt':0,
        }
        自身.会话列表.状态['ids'].append(标识)
        自身.会话列表.状态['byId'][标识]=自身.行[标识]
        if 工作区 is not None and 标识 not in 工作区['sessionIds']:
            工作区['sessionIds'].append(标识)
            自身.工作区列表.通知()
        自身.会话列表.通知()
        return 标识

    def binding(自身,标识):
        '这一代绑定。没有就空'
        return 自身.绑定.get(标识)

    def scope(自身,标识):
        '对话停止时来问作用域'
        绑定=自身.绑定.get(标识)
        return None if 绑定 is None else 绑定.ctx

    def retain(自身,目标,选项):
        '主视图持有这份会话'
        标识=目标 if isinstance(目标,str) else None
        行=自身.行.get(标识)
        if 行 is None:
            raise RuntimeError('没有会话 '+str(目标))
        来源=选项.get('source') or 'mainView'
        保留=行['retainedBy']
        保留[来源]=保留.get(来源,0)+1
        自身.会话列表.通知()
        def 放开():
            '计数减一'
            保留[来源]=保留.get(来源,0)-1
            if 保留[来源]<0:
                保留[来源]=0
            自身.会话列表.通知()
        return 保留引用(标识,放开)

    def retainInfo(自身,标识):
        '保留计数。和列表行是同一份'
        行=自身.行.get(标识)
        仓=保留仓()
        if 行 is not None:
            def 读():
                '当前保留'
                return {'retainedBy':行['retainedBy']}
            仓.getSnapshot=读
        return 仓

    def subagentAddress(自身,标识):
        '没有子会话'
        return None

    def refreshProjections(自身,标识):
        '没有远端投影可刷新'
        return None


class 会话面:
    '会话插件看到的 sessions'
    searchResultLimit=20
    def __init__(自身,宿主):
        '列表和动作都在宿主上'
        自身.list=宿主.会话列表
        自身._宿主=宿主

    def create(自身,请求=None):
        '建会话'
        return 自身._宿主.create(请求)

    def binding(自身,标识):
        '取绑定'
        return 自身._宿主.binding(标识)

    def scope(自身,标识):
        '取作用域'
        return 自身._宿主.scope(标识)

    def retain(自身,目标,选项):
        '保留'
        return 自身._宿主.retain(目标,选项)

    def retainInfo(自身,标识):
        '保留计数'
        return 自身._宿主.retainInfo(标识)

    def subagentAddress(自身,标识):
        '没有子会话'
        return 自身._宿主.subagentAddress(标识)

    def refreshProjections(自身,标识):
        '没有投影可刷新'
        return 自身._宿主.refreshProjections(标识)


class 工作区面:
    '工作区插件看到的 workspaces'
    def __init__(自身,宿主):
        '列表和默认工作区'
        自身.list=宿主.工作区列表
        自身._宿主=宿主

    def initializeDefault(自身,信号=None):
        '建默认工作区'
        return 自身._宿主.initializeDefault(信号)


class 上传服务:
    '对话插件只要求这个服务在。上传还没接到宿主'


class 目录选择器:
    '工作区导航要这个对象。目录浏览还没接上'
    def list(自身,路径,信号=None):
        '列不出'
        return {'ok':False,'error':{'message':'目录浏览还没接上'}}

    def createDirectory(自身,路径,名称):
        '建不了'
        return {'ok':False,'error':{'message':'建目录还没接上'}}


class 远程会话:
    '聊天插件的依赖名。方法还没从宿主挂上来'


class 右栏:
    '聊天插件的依赖名。右栏还没装'


class 许可源:
    '访问答案先允许。没有宿主策略'
    def getSnapshot(自身):
        '允许'
        return True

    def subscribe(自身,监听):
        '不会变'
        return lambda:None


class 访问服务:
    'ui-session 要按资源问一次许可'
    def 来源(自身,种类,标识,动作):
        '同一份允许'
        return 许可源()


class 空工作区表:
    '对话主体要读工作区列表。还没有工作区'
    def getSnapshot(自身):
        '空列表'
        return {'phase':'ready','items':[]}

    def subscribe(自身,监听):
        '不会变'
        return lambda:None


def 已有根钩子(槽,名称):
    '根贡献里已经有这个钩子'
    for 贡献 in getattr(槽,'_rootContributions',[]):
        钩子=贡献.get('hooks') if isinstance(贡献,dict) else None
        if isinstance(钩子,dict) and 名称 in 钩子:
            return True
    return False


def 装上空会话(上下文):
    '会话插件没装上时补一层空作用域。对话主体要工作区钩子'
    槽=上下文.反射.获取服务('slots',False)#槽服务
    if 槽 is None:#渲染器没起来
        return#不用装
    if 'session' not in getattr(槽,'_scopes',{}):#ui-session 没装上适配器
        def 读空():
            '当前没有会话'
            return None#空绑定
        def 订空(监听):
            '没有后续更新'
            return lambda:None#退订
        空源=可观察源(读空,订空)#快照源
        槽.installScope('session',{#session 与 session-maybe 共用
            'current':空源,#当前绑定
            'bindingSource':lambda 引用:空源,#按引用取同一份
            'renderArea':lambda *位置参数:None,#没有会话区域
        })#适配器结束
        if 已有根钩子(槽,'sessions') is False:#标题和主栏都读这个
            槽.provideRoot({'hooks':{'sessions':空会话表()}})#根上的 useSessions
    if 已有根钩子(槽,'workspaces') is False:#对话主体读这个
        槽.provideRoot({'hooks':{'workspaces':空工作区表()}})#根上的 useWorkspaces


def 源码包名():
    '启动模块在 pydsh.源码 下，插件模块也从这里装'
    return __package__.rsplit('.',2)[0]#去掉 .客户端.web


def 取插件(模块):
    '模块有 apply 就用模块。只有类的，包一层，构造时不把配置塞进只收上下文的类'
    if callable(getattr(模块,'apply',None)) or callable(getattr(模块,'应用',None)):
        return 模块#函数插件
    类=getattr(模块,'default',None)#类插件
    if not isinstance(类,type):
        raise TypeError('没有插件入口')#装不上
    def 应用(上下文,配置=None,类=类):
        '类构造只收上下文'
        类(上下文)#构造
    应用.inject=list(getattr(类,'inject',None) or getattr(模块,'依赖',None) or [])#依赖跟类走
    return 应用#函数插件


class 网页应用入口:
    '浏览器启动入口。按写死的清单在本进程挂客户端插件'
    def __init__(自身,容器,接缝=None):
        '先画出启动页'
        自身.容器=容器#应用挂载点
        自身.接缝=接缝#保留构造参数
        文档=容器.ownerDocument#这次握手的文档
        if 文档.getElementById('dsh-base') is None:#壳样式只插一次
            句柄=open(os.path.join(os.path.dirname(__file__),'基准.css'),encoding='utf-8')#壳样式
            样式=文档.createElement('style')#style
            样式.id='dsh-base'#同一份只留一次
            样式.textContent=句柄.read()#正文
            句柄.close()#关上
            文档.head.append(样式)#让 #root 撑满窗口
        自身.页=启动页(容器)#加载过程
        自身.上下文=None#挂上之后才有

    def 运行(自身,失败回调=None):
        '登记窗口，放上写死的配置，再按依赖挂名册'
        try:#整段失败留在启动页
            登记握手窗口(自身.容器.ownerDocument.defaultView)#不许另造 window
            上下文=上下文类()#本进程
            自身.上下文=上下文#拆除时用
            上下文.反射.提供服务('configForms',配置表单())#locale、theme 先读这份
            宿主=本地宿主()#这一页的工作区和会话
            上下文.反射.提供服务('sessions',会话面(宿主))#对话和会话界面读这份
            上下文.反射.提供服务('workspaces',工作区面(宿主))#工作区导航读这份
            上下文.反射.提供服务('fileUpload',上传服务())#对话的依赖
            上下文.反射.提供服务('remoteAccess',访问服务())#会话界面的依赖
            上下文.反射.提供服务('remote.directoryPicker',目录选择器())#工作区导航的依赖
            上下文.反射.提供服务('remote.session',远程会话())#聊天的依赖
            上下文.反射.提供服务('sidebarRight',右栏())#聊天的依赖
            自身.页.设总数(len(名册))#进度
            包名=源码包名()#pydsh.源码
            失败=[]#挂载会拆掉启动页，失败文案留在文档上
            for 行 in 名册:#逐行
                缺=[服务名 for 服务名 in 行['依赖'] if 上下文.反射.获取服务(服务名,False) is None]#还没挂上的依赖
                if len(缺)>0:#先不装，避免卡在等待
                    文本=行['id']+' 还没有服务 '+' '.join(缺)#原因
                    失败.append(文本)#记下
                    自身.页.设状态(行['id'],'failed',文本)#写上
                    continue#下一行
                try:#这一行
                    自身.页.设状态(行['id'],'loading')#正在装
                    模块=importlib.import_module(包名+'.'+行['模块'])#迁移后的包
                    纤程=上下文.注册表.启动插件(取插件(模块))#按 inject 挂
                    纤程.等待()#启动失败就抛
                    if 行['id']=='ui-conversation':#聊天要往这份注册表上挂消息
                        界面=上下文.反射.获取服务('uiConversation',False)#对话服务
                        if 界面 is not None:#起来了
                            上下文.反射.提供服务('conversationEvents',界面.events)#事件定义
                    自身.页.设状态(行['id'],'active')#这一行起来了
                except Exception as 错误:#这一行失败，后面能装的继续
                    文本=行['id']+'\n'+traceback.format_exc()#原因带栈
                    失败.append(文本)#记下
                    自身.页.设状态(行['id'],'failed',文本)#写上
            if 上下文.反射.获取服务('uiRenderer',False) is not None:#渲染器起来了才挂页面
                装上空会话(上下文)#根渲染要这个作用域
                挂载客户端(上下文,自身.容器)#换成应用
                宿主.retain(宿主.create({'workspaceId':'default'}),{'source':'mainView'})#打开这场空白会话
            if len(失败)>0:#启动页已经被换掉
                自身.容器.ownerDocument.documentElement.setAttribute('data-boot-error','\n'.join(失败))#留给这一页
        except Exception as 错误:#入口自己失败
            文本=traceback.format_exc()#整段栈
            try:#启动页还在就写上
                自身.页.显示失败(文本)#报告
            except Exception as 显示错误:#页面已经断开
                print(文本)#留在终端
                del 显示错误#用掉这个名字
            if 失败回调 is not None:#调用方要自己显示
                失败回调(错误)#交给它

    def 拆除(自身):
        '拆掉这次挂上的上下文'
        上下文=自身.上下文#可能还没运行
        自身.上下文=None#只拆一次
        if 上下文 is not None:#已经创建
            上下文.纤程.拆除()#插件一起走
