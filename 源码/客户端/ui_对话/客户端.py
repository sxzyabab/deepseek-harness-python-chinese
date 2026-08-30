"""会话插件浏览器半边（词表 + 骨架/聊天流槽登记）。

对齐上游 `ui-conversation/src/client/apply.ts`。公开面仅中文名。
完整 inject：根/体/页眉/栏/聊天视图/详情/审批选择器/节点回合数据。
"""
import re#绝对路径判定
from .文案 import 命名空间,中文,英文#词典
from .提交设置 import 会话设置命名空间#提交设置命名空间
from .回车行为行 import 回车行为行#设置行
from .客户端.会话根 import 会话根#骨架根
from .客户端.会话体 import 会话体,会话页眉#体/页眉
from .客户端.聊天视图 import 聊天视图#聊天
from .客户端.输入栏 import 输入栏#栏
from .客户端.统计行 import 统计行#统计
from .客户端.队列停靠 import 队列停靠条目#队列插件
from .客户端.待办面板 import 待办停靠条目#计划插件
from .客户端.审批面板 import 审批面板#审批
from .客户端.详情面板 import 详情面板#详情
from .客户端.登记节点渲染器 import 登记聊天节点渲染器#节点键
from .客户端.会话节点 import 登记会话节点#会话节点构建器
from .客户端.仓库 import 创建聊天仓库#聊天 store
from .客户端.阻断 import 阻断登记表#composer 阻断
from .客户端.提交策略 import 提交策略#提交策略
from .客户端.服务 import 会话控制器,不支持图片媒体类型#会话服务
from .客户端.输入.枢纽 import 输入枢纽#输入枢纽
from .客户端.约定.槽 import 会话根子槽#根子槽表

__all__=['注入','应用']#仅中文公开名

def 解析槽标签(标签):#读时解析可能是 thunk 的列表标签
    """对齐 ui-slots resolveSlotLabel。"""
    return 标签() if callable(标签) else 标签#值

注入=[#会话插件所需服务
    'slots','layout','sessions','workspaces','locale','connection','remote','settingsScope',
    'conversationEvents','conversationViews',
]#依赖

# 无会话时 hooks 隔间的静态源（模块常量身份，避免钩子缓存抖动）
缺席通知={'getSnapshot':lambda:None,'subscribe':lambda *_:(lambda:None)}#通知
缺席阻断={'getSnapshot':lambda:None,'subscribe':lambda *_:(lambda:None)}#阻断
空词表={}#空 / @ 词表
缺席词表={'getSnapshot':lambda:空词表,'subscribe':lambda *_:(lambda:None)}#词表
缺席菜单启动器={'getSnapshot':lambda:None,'subscribe':lambda *_:(lambda:None)}#菜单启动器

绝对路径=re.compile(r'^[A-Za-z]:[/\\]|\\\\')#盘符或 UNC

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解析工作区路径(工作目录,路径):#相对工作区根解析
    """已是绝对/UNC 或无根则原样。"""
    if 路径.startswith('/') or 绝对路径.match(路径):#绝对
        return 路径#原样
    if 工作目录 is None or 工作目录=='':#无根
        return 路径#原样
    基=工作目录.rstrip('/\\')#去尾分隔
    相对=路径.lstrip('/\\')#去头分隔
    return 基+'/'+相对#POSIX 拼

def 聊天节点回合注入():#CHAT_NODE_INJECT
    """按节点键读回合数据的钩子工厂。"""
    def 回合数据工厂(运行时,节点键):#SlotHookFactory
        """绑定 useSession。"""
        用会话=取字段(运行时,'useSession') if not isinstance(运行时,dict) else 运行时.get('useSession')#钩
        if isinstance(运行时,dict) and 用会话 is None:#可能整包是套件
            用会话=运行时.get('useSession')#再取
        def 用回合数据(键):#按 ConversationTurnDataMap 键取值
            """缺席则 None。"""
            if not callable(用会话):#无钩
                return None#无
            def 选(快照):#从会话快照取
                """回合/步骤位置才有 data。"""
                聊天=取字段(快照,'chat')#聊天
                节点表=取字段(聊天,'nodes')#节点表
                节点=None#节点
                if 节点表 is not None:#有表
                    取=getattr(节点表,'get',None)#get
                    节点=取(节点键) if callable(取) else (节点表.get(节点键) if isinstance(节点表,dict) else None)#取
                位置=取字段(节点,'location')#位置
                种=取字段(位置,'kind')#种
                if 种 not in ('turn','step'):#非回合步
                    return None#无
                回合=取字段(位置,'turn')#回合
                数据=取字段(回合,'data')#data map
                if 数据 is None:#无
                    return None#无
                取数=getattr(数据,'get',None)#get
                return 取数(键) if callable(取数) else (数据.get(键) if isinstance(数据,dict) else None)#值
            return 用会话(选)#选择器
        return 用回合数据#钩
    return {'hooks':{'turnData':回合数据工厂}}#注入

def 作用域会话(会话们,标识):#按会话作用域取 conversation
    """没有作用域或服务则大声抛。"""
    作用域=会话们.scope(标识)#作用域
    if 作用域 is None:#无
        raise Exception('ui-conversation: session "'+str(标识)+'" resolved no scope')#抛
    会话=作用域.get('conversation')#conversation
    if 会话 is None:#无
        raise Exception('ui-conversation: conversation service unavailable through the session scope')#抛
    return 会话#面

def 具体会话(上下文):#取包内控制器实现
    """公开登记转型为控制器。"""
    会话=上下文.get('conversation')#公开面
    if 会话 is None:#未挂载
        raise Exception('ui-conversation: conversation service unavailable')#抛
    return 会话#控制器

def 选审批(链属性):#链路由：审批等待未决时占用
    """纯函数 — 只用 owner props。"""
    for 项 in (取字段(链属性,'interactions') or []):#交互
        if 取字段(项,'kind')=='approval':#审批
            return 项#命中
    return None#无

def 应用(上下文):#挂载会话插件浏览器半边
    """登记词典、回车行、骨架/聊天/输入栏/统计/队列/节点键，完整 inject。"""
    会话们=上下文.sessions#会话面
    工作区们=上下文.workspaces#工作区面
    布局=上下文.layout#布局面
    槽=上下文.slots#槽登记表

    登记会话节点(上下文)#登记会话节点构建器
    登记聊天节点渲染器(上下文)#登记聊天节点渲染器
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-conversation: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定翻译

    聊天仓=创建聊天仓库()#本光纤聊天 store
    提交=提交策略(上下文.settingsScope.bind({'namespace':会话设置命名空间}))#提交策略
    聊天滚动={}#会话 id → 滚动位置
    阻断表=阻断登记表()#按会话阻断
    枢纽=输入枢纽(上下文,翻译)#每会话输入枢纽
    节点注入=聊天节点回合注入()#节点回合数据注入

    def 回车注入():#回车行注入
        """hooks + setBusyEnter。"""
        return {'hooks':{'busyEnter':提交.busyEnter},'setBusyEnter':提交.setBusyEnter}#注入
    上下文.slots.inject('settings.general.item',lambda:上下文.slots.register({#登记回车行
        'name':'settings.general.item',#通用条目
        'id':'composer-enter',#本项
        'order':20,#排序
        'locale':命名空间,#文案
        'inject':回车注入,#注入
    },回车行为行))#组件

    def 视图页签():#从 conversation.view 槽收集页签
        """id + 解析后的标签。"""
        页们=[]#累积
        for 条目 in 槽.entries('conversation.view'):#每个已登记视图
            选项=取字段(条目,'options') or 条目#选项
            标识=取字段(选项,'id')#id
            if 标识 is None:#无 id
                continue#跳过
            标签=解析槽标签(取字段(选项,'label'))#标签
            页们.append({'id':标识,'label':标签 if 标签 is not None else 标识})#页签
        return 页们#列表
    视图面={#视图环面
        'list':视图页签,#当前页签
        'subscribe':lambda 回调:槽.subscribe('conversation.view',回调),#订阅
        'version':lambda:槽.getVersion('conversation.view'),#版本
    }#面结束

    def 提供输入():#向会话作用域提供 input 标准套件
        """hooks + inputActions。"""
        def 解析(绑定):#按绑定物化
            """该会话输入壳。"""
            壳=枢纽.shellFor(绑定)#壳
            return {'hooks':{'input':壳.state},'props':{'inputActions':壳.actions}}#套件
        return 会话们.provide({'hooks':['input'],'props':['inputActions'],'resolve':解析})#提供
    if hasattr(会话们,'provide'):#有 provide
        上下文.effect(提供输入,'ui-conversation: input standard-kit provider')#挂

    def 根注入(会话标识):#conversation 根注入
        """阻断源 + 选定工作区。"""
        def 选定工作区(工作区标识):#接通并可能迁移草稿
            """空白草稿随行。"""
            下一=工作区们.connectWorkspace(工作区标识)#接通
            解开=getattr(下一,'等待',None)#承诺
            下一标识=解开() if callable(解开) else 下一#会话 id
            if 会话标识 is not None and 下一标识!=会话标识:#跨会话
                旧=枢纽.shell(会话标识)#旧壳
                草稿=取字段(旧.snapshot,'draft')#草稿
                图们=list(取字段(旧.snapshot,'imageIds') or [])#图 id
                新=枢纽.shell(下一标识)#新壳
                if len(图们)==0 or 新.addImages(图们):#无图或收下
                    if 草稿!='':#有文
                        新.setDraft(草稿)#迁文
                        旧.setDraft('')#清空旧
                    for 图标识 in 图们:#摘图
                        旧.removeImage(图标识)#移除
            会话们.open(下一标识)#打开
        阻断源=缺席阻断 if 会话标识 is None else 阻断表.storeFor(会话标识)#阻断
        return {'hooks':{'composerBlock':阻断源},'selectWorkspace':选定工作区}#注入
    槽.register({#登记会话根
        'name':'conversation',#根
        'locale':命名空间,#文案
        'children':dict(会话根子槽),#子槽
        'inject':根注入,#注入
    },会话根)#根组件

    def 体注入(会话标识,_动作=None):#会话体注入
        """视图环 + 释放图 + 草稿镜像。"""
        控制器=具体会话(上下文)#控制器
        return {#体面
            'views':视图面,#视图
            'releaseSessionImages':lambda 标识:控制器.releaseSessionImages(标识),#释放图
            'bindDraftMirror':lambda 写出:枢纽.shell(会话标识).bindMirror(写出),#镜像
        }#返回
    槽.register({#登记会话体
        'name':'conversation.session',#体
        'children':{'conversation.view':{'kind':'list','scope':'session'}},#视图环
        'store':聊天仓,#共享 store
        'inject':体注入,#注入
    },会话体)#体组件

    def 页眉注入(_会话标识=None,_动作=None):#页眉注入
        """视图环 + 打开会话。"""
        return {'views':视图面,'open':lambda 标识:会话们.open(标识)}#注入
    槽.register({#登记页眉
        'name':'conversation.session.header',#页眉
        'locale':命名空间,#文案
        'children':{#子
            'conversation.session.header.actions':{'kind':'list','scope':'session'},#动作
            'conversation.session.header.utilities':{'kind':'list','scope':'session'},#工具
        },#子结束
        'store':聊天仓,#共享 store
        'inject':页眉注入,#注入
    },会话页眉)#页眉组件

    def 栏注入(会话标识):#composer 栏注入
        """无会话则静态空源。"""
        if 会话标识 is None:#无会话
            return {#静态空
                'keyboard':None,#无键盘
                'addImages':None,#无加图
                'removeImage':None,#无摘图
                'draftImages':None,#无草稿图
                'resolveSubmitMode':lambda 忙碌,手势,可转向:提交.resolve(忙碌,手势,可转向),#策略
                'toggleCommandMenu':None,#无菜单
                'stop':None,#无停止
                'command':None,#无命令
                'hooks':{'notices':缺席通知,'lexicon':缺席词表,'menuLauncher':缺席菜单启动器},#空 hooks
            }#结束
        控制器=具体会话(上下文)#控制器
        壳=枢纽.shell(会话标识)#壳
        触发=枢纽.inputTriggers(会话标识)#触发器
        def 加图(文件们):#铸造并挂图
            """不支持类型返回文案。"""
            try:#铸造
                图们=控制器.createDraftImages(文件们)#铸造
                if not 壳.addImages([取字段(图,'id') for 图 in 图们]):#拒绝
                    控制器.releaseDraftImages(图们)#释放
                return None#无错
            except 不支持图片媒体类型:#不支持
                return 翻译('image.unsupportedType')#文案
            except Exception as 错:#其它
                return str(错)#信息
        def 摘图(标识):#摘一张
            """释放附件并从壳去掉。"""
            控制器.releaseDraftImage(标识)#释放
            壳.removeImage(标识)#去掉
        def 切命令菜单(选区):#切换斜杠菜单
            """先关弹层再 toggle command 源。"""
            壳.dismissPopup()#关弹层
            快=壳.snapshot#快照
            前=快['draft'][:取字段(选区,'start',0)].strip()#光标前
            触发.toggleSource('command',{#切换
                'trigger':'/',#触发符
                'query':'',#空查询
                'position':'leading' if 前=='' else 'inline',#行首或行内
                'span':{**选区,'draftRev':快['draftRev']},#跨度
            })#结束
        def 停止():#取消进行中回合
            """失败不抛给 UI。"""
            try:#取消
                作用域会话(会话们,会话标识).cancel()#取消
            except Exception:#失败
                pass#经 promptError 露出
        def 命令(行):#跑斜杠命令
            """成功且命中才 True。"""
            绑定=会话们.binding(会话标识)#绑定
            会话=取字段(绑定,'session') if 绑定 is not None else None#会话
            if 会话 is None:#无
                return False#未匹配
            结果=会话.command(行)#派发
            等待=getattr(结果,'等待',None)#承诺
            结果=等待() if callable(等待) else 结果#解开
            return 取字段(结果,'ok') is True and 取字段(取字段(结果,'value'),'matched') is True#命中
        启动器=取字段(触发,'launcher') if 触发 is not None else None#启动器
        return {#有会话栏面
            'keyboard':壳,#键盘面
            'addImages':加图,#加图
            'removeImage':摘图,#摘图
            'draftImages':lambda 标识们:控制器.draftImages(标识们),#读草稿图
            'resolveSubmitMode':lambda 忙碌,手势,可转向:提交.resolve(忙碌,手势,可转向),#策略
            'toggleCommandMenu':None if 触发 is None else 切命令菜单,#菜单
            'stop':停止,#停止
            'command':命令,#命令
            'hooks':{#外部源
                'notices':壳.notices,#通知
                'lexicon':壳.lexicon,#词表
                'menuLauncher':启动器 if 启动器 is not None else 缺席菜单启动器,#启动器
            },#hooks 结束
        }#返回
    槽.register({#登记 composer 栏
        'name':'conversation.composer.bar',#栏
        'locale':命名空间,#文案
        'children':{#子席
            'conversation.input.plan':{'kind':'single','scope':'session'},#计划
            'conversation.input.model':{'kind':'single','scope':'session'},#模型
        },#子结束
        'inject':栏注入,#注入
    },输入栏)#栏组件

    槽.register({#审批接管
        'name':'conversation.composer',#链
        'select':选审批,#选择器
        'priority':1,#优先于提问默认 0
        'locale':命名空间,#文案
    },审批面板)#审批

    def 聊天注入(会话标识,动作):#聊天视图注入
        """详情/文件/历史/检查/滚动/分叉。"""
        控制器=具体会话(上下文)#控制器
        作用域面=作用域会话(会话们,会话标识)#作用域 conversation
        仓动作=动作 if 动作 is not None else 聊天仓#动作面
        def 打开详情(目标):#打开详情
            """选定并打开详情栏。"""
            仓动作.select(目标)#选定
            布局.openDetails()#打开
        def 打开文件(路径):#打开工作区路径
            """宿主打开失败静默。"""
            列表=会话们.list.getSnapshot() if hasattr(会话们,'list') else None#列表
            摘要=取字段(取字段(列表,'byId'),会话标识) if 列表 is not None else None#摘要
            工作目录=取字段(摘要,'cwd')#cwd
            try:#打开
                工作区们.openPath(解析工作区路径(工作目录,路径))#打开
            except Exception:#失败
                pass#静默
        def 检视调用(调用标识):#切轨迹并盯住
            """未登记 trajectory 则环回退。"""
            仓动作.setInspect({'callId':调用标识})#记下
            仓动作.setView('trajectory')#切视图
        def 存滚动(位置):#保存或清除
            """null 丢掉记忆。"""
            if 位置 is None:#清
                聊天滚动.pop(会话标识,None)#删
            else:#记
                聊天滚动[会话标识]=位置#写
        def 读滚动():#读上次
            """没有则 None。"""
            return 聊天滚动.get(会话标识)#位置
        def 分叉(序号):#在该序号分叉
            """失败保持源视图。"""
            try:#分叉
                子=会话们.fork({'sessionId':会话标识,'atSeq':序号,'increaseTitle':True})#分叉
                等待=getattr(子,'等待',None)#承诺
                子标识=等待() if callable(等待) else 子#子 id
                会话们.open(子标识)#打开
            except Exception:#失败
                pass#不动
        def 文件提及(属主):#收口提及
            """可选 chatFileMentions 服务。"""
            服务=上下文.get('chatFileMentions')#服务
            if 服务 is None:#缺席
                return None#无
            取=getattr(服务,'forClosing',None)#forClosing
            return 取(属主) if callable(取) else None#词表
        return {#聊天视图片
            'openDetails':打开详情,#详情
            'fileMentions':文件提及,#提及
            'openFile':打开文件,#打开文件
            'loadOlder':lambda:作用域面.loadOlder(),#更早历史
            'loadImage':lambda 附件:控制器.resolveImage(会话标识,附件),#历史图
            'inspectCall':检视调用,#检视
            'chatScroll':{'save':存滚动,'read':读滚动},#滚动
            'forkAt':分叉,#分叉
        }#返回
    槽.register({#登记聊天视图
        'name':'conversation.view',#视图
        'id':'chat',#id
        'order':0,#序
        'label':lambda:翻译('view.chat'),#标签
        'locale':命名空间,#文案
        'children':{#子
            'conversation.chat.node':{'kind':'keyed','scope':'session','inject':节点注入},#节点席
        },#子结束
        'store':聊天仓,#共享 store
        'inject':聊天注入,#注入
    },聊天视图)#聊天组件

    槽.register({#统计行
        'name':'conversation.composer.dock',#停靠
        'id':'stats',#id
        'order':0,#序
        'locale':命名空间,#文案
    },统计行)#统计

    上下文.plugin(会话控制器,{'input':枢纽,'blocks':阻断表})#挂载会话控制器
    上下文.plugin(待办停靠条目)#计划停靠
    上下文.plugin(队列停靠条目)#队列停靠

    def 详情注入(_会话标识=None,_动作=None):#详情注入
        """关闭详情栏。"""
        return {'closeDetails':lambda:布局.closeDetails()}#注入
    槽.register({#登记详情
        'name':'details',#详情
        'locale':命名空间,#文案
        'children':{'conversation.details.tool':{'kind':'single','scope':'session'}},#工具席
        'store':聊天仓,#共享 store
        'inject':详情注入,#注入
    },详情面板)#详情
