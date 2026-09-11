"""会话浏览器半公开面。

对齐上游 `ui-conversation/src/client/index.ts` 可 Python 化部分。公开面仅中文名。
输入机全量与会话节点构建器本轮已落。浏览器半边 `应用` 登记词表、骨架与停靠插件。
"""
import re#绝对路径判定
from ..提交设置 import 会话设置命名空间#提交设置命名空间
from ..回车行为行 import 回车行为行#设置行
from .文案 import 命名空间,中文,英文#词典
from .存储 import 创建聊天存储#聊天存储
from .阻断 import 阻断登记表#阻断
from .提交策略 import 提交策略,默认忙碌回车行为#提交策略
from .服务 import 会话控制器,不支持图片媒体类型,对话错误#会话服务
from .会话根 import 会话根,派生阶段#骨架根
from .会话面板 import 会话面板#主面板
from .会话体 import 会话体,会话页眉#严格会话体与页眉
from .空白英雄 import 工作区芯片,英雄辉光,英雄壳#英雄铬
from .输入栏 import 输入栏#composer 栏
from .审批面板 import 审批面板,待决审批#审批接管
from .上下文仪表 import 上下文仪表#占用环
from .详情面板 import 详情面板#详情列
from .待办面板 import 待办面板,待办停靠,待办停靠条目#计划条
from .权限选择 import 权限选择#访问模式
from .聊天视图 import 聊天视图#聊天流
from .聊天节点席 import 聊天节点席#节点席
from .节点席 import 节点席#节点席别名面
from .消息项 import 用户消息行,模型重试行,回合错行,回合顶格行,待插话泡#消息行
from .助手节点视图 import 助手节点视图#助手
from .助手Markdown import 助手Markdown#块体
from .消息铬 import 格式化运行时长,格式化消息时钟#时间标签
from .统计行 import 统计行,上下文占用,格式化令牌#统计
from .工具节点读取 import 根工具调用,查找工具调用#工具查找
from .登记节点渲染器 import 登记聊天节点渲染器#登记
from .队列停靠 import 队列停靠,队列停靠条目#队列
from .输入 import (#输入机子包
    输入机,会话输入壳,输入枢纽,投影剪贴板,派生装饰,空输入状态,占位符,
)#输入结束
from .会话节点 import 登记会话节点#会话节点
from .约定.槽 import 会话根子槽#根子槽表

__all__=[#仅中文公开名
    '注入','应用',
    '命名空间','中文','英文',
    '创建聊天存储','阻断登记表','提交策略','默认忙碌回车行为',
    '会话控制器','不支持图片媒体类型','对话错误',
    '会话根','派生阶段','会话面板','会话页眉','会话体',
    '工作区芯片','英雄辉光','英雄壳','输入栏',
    '审批面板','待决审批','上下文仪表','详情面板',
    '待办面板','待办停靠','待办停靠条目','权限选择',
    '聊天视图','聊天节点席','节点席','助手节点视图','助手Markdown',
    '用户消息行','模型重试行','回合错行','回合顶格行','待插话泡',
    '格式化运行时长','格式化消息时钟','统计行','上下文占用','格式化令牌',
    '根工具调用','查找工具调用','登记聊天节点渲染器','队列停靠','队列停靠条目',
    '输入机','会话输入壳','输入枢纽','投影剪贴板','派生装饰','空输入状态','占位符',
    '登记会话节点',
]#公开面结束

注入=[#会话插件所需服务
    'slots','layout','sessions','workspaces','locale','connection','remote','settingsScope',
    'conversationEvents','conversationViews',
]#依赖

绝对路径=re.compile(r'^[A-Za-z]:[/\\]|\\\\')#盘符或 UNC

空词表={}#空 / @ 词表

def 空拆除():
    """空订阅无可拆。"""
    return None#无事

def 空快照():
    """缺席源快照恒为 None。"""
    return None#无

def 空订(*位置参数):
    """缺席源不通知。"""
    return 空拆除#拆除器

def 空词表快照():
    """缺席词表恒为空表。"""
    return 空词表#空

缺席通知={'getSnapshot':空快照,'subscribe':空订}#通知
缺席阻断={'getSnapshot':空快照,'subscribe':空订}#阻断
缺席词表={'getSnapshot':空词表快照,'subscribe':空订}#词表
缺席菜单启动器={'getSnapshot':空快照,'subscribe':空订}#菜单启动器

def 解析槽标签(标签):
    """对齐 ui-slots resolveSlotLabel。字面量或零参 thunk。"""
    if 标签 is None:#未声明
        return None#缺席
    if isinstance(标签,str):#字面量
        return 标签#值
    return 标签()#thunk

def 解析工作区路径(工作目录,路径):
    """已是绝对/UNC 或无根则原样。"""
    if 路径.startswith('/') or 绝对路径.match(路径) is not None:#绝对
        return 路径#原样
    if 工作目录 is None or 工作目录=='':#无根
        return 路径#原样
    基=工作目录.rstrip('/\\')#去尾分隔
    相对=路径.lstrip('/\\')#去头分隔
    return 基+'/'+相对#POSIX 拼

def 选聊天(快照):
    """快照.chat。快照为 dict。"""
    return 快照['chat'] if 'chat' in 快照 else None#聊天

def 造聊天节点回合注入():
    """按节点键读回合数据的钩子工厂。节点仓为契约 dict。"""
    def 回合数据工厂(运行时,节点键):
        """绑定 useSession。运行时为槽 props dict。"""
        用会话=运行时['useSession'] if 'useSession' in 运行时 else None#钩
        def 用回合数据(键):
            """缺席则 None。"""
            if 用会话 is None:#无钩
                return None#无
            def 选(快照):
                """回合/步骤位置才有 data。"""
                聊天=快照['chat'] if 'chat' in 快照 else None#聊天
                节点表=聊天['nodes'] if 聊天 is not None and 'nodes' in 聊天 else None#节点表
                if 节点表 is None:#无表
                    return None#无
                节点=节点表['get'](节点键)#仓 get
                位置=节点['location'] if 节点 is not None and 'location' in 节点 else None#位置
                种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#种
                if 种 not in ('turn','step'):#非回合步
                    return None#无
                回合=位置['turn'] if 'turn' in 位置 else None#回合
                if 回合 is None:#无
                    return None#无
                数据=回合['data'] if 'data' in 回合 else None#data map
                if 数据 is None:#无
                    return None#无
                return 数据[键] if 键 in 数据 else None#值
            return 用会话(选)#选择器
        return 用回合数据#钩
    return {'hooks':{'turnData':回合数据工厂}}#注入

def 作用域会话(会话面,标识):
    """没有作用域或服务则大声抛。"""
    作用域=会话面.scope(标识)#作用域
    if 作用域 is None:#无
        raise 对话错误('ui-conversation: session "'+str(标识)+'" resolved no scope')#抛
    会话=作用域.获取服务('conversation')#conversation
    if 会话 is None:#无
        raise 对话错误('ui-conversation: conversation service unavailable through the session scope')#抛
    return 会话#面

def 具体会话(上下文):
    """公开登记转型为控制器。"""
    会话=上下文.获取服务('conversation')#公开面
    if 会话 is None:#未挂载
        raise 对话错误('ui-conversation: conversation service unavailable')#抛
    return 会话#控制器

def 选审批(链属性):
    """纯函数 — 只用 owner props。链属性为 dict。"""
    交互=链属性['interactions'] if 'interactions' in 链属性 else None#交互
    列=交互 if 交互 is not None else []#空则空表
    for 项 in 列:#交互
        if ('kind' in 项) and 项['kind']=='approval':#审批
            return 项#命中
    return None#无

def 应用(上下文):
    """登记词典、回车行、骨架/聊天/输入栏/统计/队列/节点键，完整依赖启动。"""
    会话面=上下文.sessions#会话面
    工作区面=上下文.workspaces#工作区面
    工作区导航=上下文.获取服务('uiWorkspace')#工作区 UI 导航（openSession）
    布局=上下文.layout#布局面
    槽=上下文.slots#槽登记表
    登记会话节点(上下文)#登记会话节点构建器
    登记聊天节点渲染器(上下文)#登记聊天节点渲染器
    def 登记词典():
        """登记本包词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'ui-conversation: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定翻译
    聊天存储=创建聊天存储()#本光纤聊天存储
    提交=提交策略(上下文.settingsScope.bind({'namespace':会话设置命名空间}))#提交策略
    聊天滚动={}#会话 id → 滚动位置
    阻断表=阻断登记表()#按会话阻断
    枢纽=输入枢纽(上下文,翻译)#每会话输入枢纽
    节点注入=造聊天节点回合注入()#节点回合数据注入
    def 登记文件动作(作用域):
        """等 commandUi 后登记 file 动作。"""
        命令=作用域.get('commandUi')#命令面
        def 挂文件():
            """登记 /file 动作。"""
            def 标题():
                """本地化文件标题。"""
                return 翻译('input.file')#标题
            def 可用(会话):
                """作曲器是否接受文件。会话为 dict。"""
                return 枢纽.canPickFiles(会话['sessionId'])#可用性
            def 跑(会话):
                """打开文件选择。会话为 dict。"""
                枢纽.pickFiles(会话['sessionId'])#打开
            return 命令.register({#贡献
                'name':'file',#命令名
                'label':标题,#本地化标题
                'icon':'IconPaperclipOutline16',#回形针字形名
                'available':可用,#作曲器是否接受文件
                'ui':{'kind':'action','run':跑},#打开文件选择
            })#登记结束
        作用域.副作用(挂文件,'ui-conversation: File action')#挂
    上下文.inject(['commandUi'],登记文件动作)#等 commandUi
    def 回车注入():
        """hooks + setBusyEnter。"""
        return {'hooks':{'busyEnter':提交.busyEnter},'setBusyEnter':提交.setBusyEnter}#注入
    def 登记回车行():
        """忙碌 Enter 行。"""
        return 上下文.slots.register({#登记回车行
            'name':'settings.general.item',#通用条目
            'id':'composer-enter',#本项
            'order':20,#排序
            'locale':命名空间,#文案
            'inject':回车注入,#注入
        },回车行为行)#组件
    上下文.slots.inject('settings.general.item',登记回车行)#挂
    def 视图页签():
        """id + 解析后的标签。条目为 dict。"""
        页列表=[]#累积
        for 条目 in 槽.entries('conversation.view'):#每个已登记视图
            选项=条目['options'] if 'options' in 条目 else 条目#选项
            标识=选项['id'] if 'id' in 选项 else None#id
            if 标识 is None:#无 id
                continue#跳过
            标签=解析槽标签(选项['label'] if 'label' in 选项 else None)#标签
            页列表.append({'id':标识,'label':标签 if 标签 is not None else 标识})#页签
        return 页列表#列表
    def 订视图(回调):
        """订 conversation.view。"""
        return 槽.subscribe('conversation.view',回调)#订阅
    def 视图版本():
        """conversation.view 版本。"""
        return 槽.getVersion('conversation.view')#版本
    视图面={#视图环面
        'list':视图页签,#当前页签
        'subscribe':订视图,#订阅
        'version':视图版本,#版本
    }#面结束
    def 提供输入():
        """向会话作用域提供 input 标准套件。"""
        def 解析(绑定):
            """该会话输入壳。"""
            壳=枢纽.shellFor(绑定)#壳
            return {'hooks':{'input':壳.state},'props':{'inputActions':壳.actions}}#套件
        return 会话面.provide({'hooks':['input'],'props':['inputActions'],'resolve':解析})#提供
    上下文.副作用(提供输入,'ui-conversation: input standard-kit provider')#挂
    def 根注入(会话标识):
        """阻断源 + 选定工作区（经 openWorkspace，打开前迁移草稿）。"""
        def 选定工作区(工作区标识):
            """空白草稿随行；openWorkspace 在打开前调用 beforeOpen。"""
            def 打开前(下一标识):
                """跨会话迁移草稿与附件。"""
                if 会话标识 is None or 下一标识==会话标识:#同会话
                    return#无需
                旧=枢纽.shell(会话标识)#旧壳
                快=旧.snapshot#快照 dict
                草稿=快['draft'] if 'draft' in 快 else ''#草稿
                附件列=快['attachmentIds'] if 'attachmentIds' in 快 else (快['imageIds'] if 'imageIds' in 快 else None)#附件
                附件列表=list(附件列) if 附件列 is not None else []#附件表
                新=枢纽.shell(下一标识)#新壳
                加附=新.addAttachments if hasattr(新,'addAttachments') else (新.addImages if hasattr(新,'addImages') else None)#加附件
                摘附=旧.removeAttachment if hasattr(旧,'removeAttachment') else (旧.removeImage if hasattr(旧,'removeImage') else None)#摘附件
                可迁=len(附件列表)==0 or (加附 is not None and 加附(附件列表))#无附或收下
                if not 可迁:#拒收
                    return#止
                if 会话面.binding(下一标识) is None:#须有绑定
                    raise Exception('ui-conversation: session "'+str(下一标识)+'" resolved no binding')#抛
                控制器=具体会话(上下文)#控制器
                if hasattr(控制器,'rebindDraftFiles'):#重绑
                    控制器.rebindDraftFiles(下一标识,附件列表)#重绑
                if 草稿!='':#有文
                    新.setDraft(草稿)#迁文
                    旧.setDraft('')#清空旧
                if 摘附 is not None:#可摘
                    for 附标识 in 附件列表:#摘
                        摘附(附标识)#移除
            打开=工作区导航.openWorkspace if 工作区导航 is not None else 工作区面.openWorkspace#打开工作区
            结果=打开(工作区标识,打开前)#打开；导航面优先
            if hasattr(结果,'等待'):#任务面
                结果.等待()#等连接打开
        阻断源=缺席阻断 if 会话标识 is None else 阻断表.storeFor(会话标识)#阻断
        return {'hooks':{'composerBlock':阻断源},'selectWorkspace':选定工作区}#注入
    def 体注入(会话标识,_动作=None):
        """视图环 + 释放图 + 草稿镜像。"""
        控制器=具体会话(上下文)#控制器
        def 释放图(标识):
            """释放该会话草稿图。"""
            return 控制器.releaseSessionImages(标识)#释放图
        def 绑镜像(写出):
            """草稿镜像到仓。"""
            return 枢纽.shell(会话标识).bindMirror(写出)#镜像
        return {#体面
            'views':视图面,#视图
            'releaseSessionImages':释放图,#释放图
            'bindDraftMirror':绑镜像,#镜像
        }#返回
    def 打开会话(标识):
        """经工作区 UI 打开会话。"""
        if 工作区导航 is not None:#有 uiWorkspace
            return 工作区导航.openSession(标识)#导航打开
        return 会话面.open(标识)#回退会话面
    def 页眉注入(_会话标识=None,_动作=None):
        """视图环 + 打开会话。"""
        return {'views':视图面,'open':打开会话}#注入
    def 栏注入(会话标识):
        """无会话则静态空源；hooks 含 busyEnter。"""
        if 会话标识 is None:#无会话
            return {#静态空
                'keyboard':None,#无键盘
                'addImages':None,#无加图
                'removeImage':None,#无摘图
                'draftImages':None,#无草稿图
                'toggleCommandMenu':None,#无菜单
                'stop':None,#无停止
                'command':None,#无命令
                'hooks':{#空 hooks
                    'busyEnter':提交.busyEnter,#忙碌 Enter 仍可订阅
                    'notices':缺席通知,#通知
                    'lexicon':缺席词表,#词表
                    'menuLauncher':缺席菜单启动器,#启动器
                },#hooks 结束
            }#结束
        控制器=具体会话(上下文)#控制器
        壳=枢纽.shell(会话标识)#壳
        触发=枢纽.inputTriggers(会话标识)#触发器
        def 加图(文件列表):
            """不支持类型返回文案。"""
            try:#铸造
                图列表=控制器.createDraftImages(文件列表)#铸造
                标识列表=[]#id
                for 图 in 图列表:#逐图
                    标识列表.append(图['id'] if 'id' in 图 else None)#id
                if 壳.addImages(标识列表) is False:#拒绝
                    控制器.releaseDraftImages(图列表)#释放
                return None#无错
            except 不支持图片媒体类型:#不支持
                return 翻译('image.unsupportedType')#文案
            except 对话错误 as 错:#本包失败
                return str(错)#信息
            except Exception as 错:#RPC/宿主未定契约，收不窄
                return str(错)#信息
        def 摘图(标识):
            """释放附件并从壳去掉。"""
            控制器.releaseDraftImage(标识)#释放
            壳.removeImage(标识)#去掉
        def 切命令菜单(选区):
            """先关弹层再 toggle command 源。选区为 dict。"""
            壳.dismissPopup()#关弹层
            快=壳.snapshot#快照
            起点=选区['start'] if 'start' in 选区 else 0#光标
            前=快['draft'][:起点].strip()#光标前
            触发.toggleSource('command',{#切换
                'trigger':'/',#触发符
                'query':'',#空查询
                'position':'leading' if 前=='' else 'inline',#行首或行内
                'span':{**选区,'draftRev':快['draftRev']},#跨度
            })#结束
        def 停止():
            """失败不抛给 UI。"""
            try:#取消
                作用域会话(会话面,会话标识).cancel()#取消
            except 对话错误:#本包失败
                pass#经 promptError 露出
        def 命令(行):
            """成功且命中才 True。command 返回任务。"""
            绑定=会话面.binding(会话标识)#绑定
            会话=绑定.session if 绑定 is not None else None#会话
            if 会话 is None:#无
                return False#未匹配
            结果=会话.command(行).等待()#派发
            if 结果['ok'] is not True:#失败
                return False#未命中
            值=结果['value'] if 'value' in 结果 else None#值
            return 值 is not None and ('matched' in 值) and 值['matched'] is True#命中
        def 读草稿图(标识列表):
            """读草稿图。"""
            return 控制器.draftImages(标识列表)#读
        启动器=触发.launcher if 触发 is not None else None#启动器
        return {#有会话栏面
            'keyboard':壳,#键盘面
            'addImages':加图,#加图
            'removeImage':摘图,#摘图
            'draftImages':读草稿图,#读草稿图
            'toggleCommandMenu':None if 触发 is None else 切命令菜单,#菜单
            'stop':停止,#停止
            'command':命令,#命令
            'hooks':{#外部源
                'busyEnter':提交.busyEnter,#忙碌 Enter 偏好
                'notices':壳.notices,#通知
                'lexicon':壳.lexicon,#词表
                'menuLauncher':启动器 if 启动器 is not None else 缺席菜单启动器,#启动器
            },#hooks 结束
        }#返回
    def 挂主与会话壳():
        """等 main 洞就绪后登记会话面板与子槽。"""
        拆面板=槽.register({#主面板占位
            'name':'main',#主洞
            'key':'conversation',#本实现键
            'children':{'main.conversation':{'kind':'single','scope':'session-maybe'}},#会话根子洞
        },会话面板)#面板组件
        拆根=槽.register({#登记会话根
            'name':'main.conversation',#根
            'locale':命名空间,#文案
            'children':dict(会话根子槽),#子槽
            'inject':根注入,#注入
        },会话根)#根组件
        拆体=槽.register({#登记会话体
            'name':'conversation.session',#体
            'children':{'conversation.view':{'kind':'list','scope':'session'}},#视图环
            'store':聊天存储,#共享 store
            'inject':体注入,#注入
        },会话体)#体组件
        拆页眉=槽.register({#登记页眉
            'name':'conversation.session.header',#页眉
            'locale':命名空间,#文案
            'children':{#子
                'conversation.session.header.actions':{'kind':'list','scope':'session'},#动作
                'conversation.session.header.utilities':{'kind':'list','scope':'session'},#工具
            },#子结束
            'store':聊天存储,#共享 store
            'inject':页眉注入,#注入
        },会话页眉)#页眉组件
        拆栏=槽.register({#登记 composer 栏
            'name':'conversation.composer.bar',#栏
            'locale':命名空间,#文案
            'children':{#子席
                'conversation.input.plan':{'kind':'single','scope':'session'},#计划
                'conversation.input.model':{'kind':'single','scope':'session'},#模型
            },#子结束
            'inject':栏注入,#注入
        },输入栏)#栏组件
        def 拆():
            """逆序拆。"""
            拆栏()#栏
            拆页眉()#页眉
            拆体()#体
            拆根()#根
            拆面板()#面板
        return 拆#拆除器
    槽.inject('main',挂主与会话壳)#等 main 洞
    槽.register({#审批接管
        'name':'conversation.composer',#链
        'select':选审批,#选择器
        'priority':1,#优先于提问默认 0
        'locale':命名空间,#文案
    },审批面板)#审批
    def 聊天注入(会话标识,动作):
        """详情/文件/历史/检查/滚动/分叉。"""
        控制器=具体会话(上下文)#控制器
        作用域面=作用域会话(会话面,会话标识)#作用域 conversation
        仓动作=动作 if 动作 is not None else 聊天存储#动作面
        def 打开详情(目标):
            """选定并打开详情栏。"""
            仓动作.select(目标)#选定
            布局.openDetails()#打开
        def 打开文件(路径):
            """宿主打开失败静默。"""
            列表=会话面.list.getSnapshot()#列表
            册=列表['byId'] if 列表 is not None and 'byId' in 列表 else None#byId
            摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
            工作目录=摘要['cwd'] if 摘要 is not None and 'cwd' in 摘要 else None#cwd
            try:#打开
                工作区面.openPath(解析工作区路径(工作目录,路径))#打开
            except Exception:#RPC/宿主未定契约，收不窄
                pass#静默
        def 检视调用(调用标识):
            """未登记 trajectory 则环回退。"""
            仓动作.setInspect({'callId':调用标识})#记下
            仓动作.setView('trajectory')#切视图
        def 存滚动(位置):
            """null 丢掉记忆。"""
            if 位置 is None:#清
                聊天滚动.pop(会话标识,None)#删
            else:#记
                聊天滚动[会话标识]=位置#写
        def 读滚动():
            """没有则 None。"""
            return 聊天滚动[会话标识] if 会话标识 in 聊天滚动 else None#位置
        def 分叉(序号):
            """失败保持源视图。fork 返回任务。"""
            try:#分叉
                子标识=会话面.fork({'sessionId':会话标识,'atSeq':序号,'increaseTitle':True}).等待()#子 id
                会话面.open(子标识)#打开
            except Exception:#RPC/宿主未定契约，收不窄
                pass#不动
        def 文件提及(属主):
            """可选 chatFileMentions 服务。"""
            服务=上下文.获取服务('chatFileMentions')#服务
            if 服务 is None:#缺席
                return None#无
            return 服务.forClosing(属主)#词表
        def 加载更早():
            """更早历史。"""
            return 作用域面.loadOlder()#更早
        def 加载图(附件):
            """历史图。"""
            return 控制器.resolveImage(会话标识,附件)#图
        return {#聊天视图片
            'openDetails':打开详情,#详情
            'fileMentions':文件提及,#提及
            'openFile':打开文件,#打开文件
            'loadOlder':加载更早,#更早历史
            'loadImage':加载图,#历史图
            'inspectCall':检视调用,#检视
            'chatScroll':{'save':存滚动,'read':读滚动},#滚动
            'forkAt':分叉,#分叉
        }#返回
    def 聊天标签():
        """视图标签。"""
        return 翻译('view.chat')#标签
    槽.register({#登记聊天视图
        'name':'conversation.view',#视图
        'id':'chat',#id
        'order':0,#序
        'label':聊天标签,#标签
        'locale':命名空间,#文案
        'children':{#子
            'conversation.chat.node':{'kind':'keyed','scope':'session','inject':节点注入},#节点席
        },#子结束
        'store':聊天存储,#共享 store
        'inject':聊天注入,#注入
    },聊天视图)#聊天组件
    槽.register({#统计行
        'name':'conversation.composer.dock',#停靠
        'id':'stats',#id
        'order':0,#序
        'locale':命名空间,#文案
    },统计行)#统计
    上下文.启动插件(会话控制器,{'input':枢纽,'blocks':阻断表})#挂载会话控制器
    上下文.启动插件(待办停靠条目)#计划停靠
    上下文.启动插件(队列停靠条目)#队列停靠
    def 关详情():
        """关闭详情栏。"""
        return 布局.closeDetails()#关
    def 详情注入(_会话标识=None,_动作=None):
        """关闭详情栏。"""
        return {'closeDetails':关详情}#注入
    槽.register({#登记详情
        'name':'details',#详情
        'locale':命名空间,#文案
        'children':{'conversation.details.tool':{'kind':'single','scope':'session'}},#工具席
        'store':聊天存储,#共享 store
        'inject':详情注入,#注入
    },详情面板)#详情

inject=注入#框架槽
apply=应用#框架槽
