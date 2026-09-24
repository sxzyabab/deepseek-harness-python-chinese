import threading#分叉后台观察
from urllib.parse import quote as 百分编码#URI 段编码
import 客户端.ui_侧边栏_文档预览.客户端 as _侧边栏文档预览#文档预览面：SidebarRightResourceParamsMap.file
from ..聊天设置 import 聊天设置命名空间,默认链接打开#Chat 设置段
from .文案 import 命名空间,中文,英文#词典
from .存储 import 创建聊天存储#选中存储
from .转录视图 import 转录视图策略#呈现策略
from .呈现策略 import 派生呈现策略
from .性能用量 import 性能用量策略
from .约定.快照 import 空聊天快照#空快照
from .聊天.用回合数据 import 用回合数据值#回合数据
from .聊天.用披露 import 绑定披露
from .聊天.登记节点渲染器 import 登记聊天节点渲染器#节点渲染器
from .聊天.聊天视图 import 聊天视图#Chat 视图
from .聊天.统计行 import 统计行#统计
from .聊天.审批命令 import 审批命令#审批卡
from .详情.详情面板 import 详情面板#详情
from .设置.转录视图行 import 转录视图行#设置行
from .会话节点 import 登记会话节点#会话节点
from ...存储 import 创建快照存储
from .会话节点.节点工厂 import 聊天错误#本包异常

_=_侧边栏文档预览#保活侧效导入

__all__=['依赖','应用']#仅中文公开名

依赖=[#前置 inject
    'slots','sessions','uiWorkspace','uiSession','uiConversation','layout','locale',
    'settingsScope','remote','remote.session','sidebarRight',
]#依赖

def 造回合数据(_标准,数据):
    """按节点读回合数据。"""
    def 读键(键):
        """读一键。"""
        return 用回合数据值(数据,键)#值
    return 读键#工厂

def 造披露(_标准,数据):
    """到组件调用前不订阅。"""
    return 绑定披露(数据['disclosureReset'])

聊天节点注入={#CHAT_NODE_INJECT
    'hooks':{#钩子
        'turnData':造回合数据,#回合数据
        'disclosure':造披露,#披露
    },#hooks 结束
}#注入结束

def 编码段(段):
    """百分编码一段，冒号保持字面量。"""
    return 百分编码(段,safe='').replace('%3A',':').replace('%3a',':')#冒号原样

def 编码路径(路径):
    """按斜杠分段编码。"""
    return '/'.join(编码段(段) for 段 in 路径.split('/'))#分段

def 是否绝对工作区路径(路径):
    """POSIX 根、Windows 盘符或 UNC。"""
    if 路径.startswith('/'):
        return True#POSIX 绝对
    if 路径.startswith('\\\\'):
        return True#UNC
    if len(路径)>=3 and 路径[0].isalpha() and 路径[1]==':' and 路径[2] in '/\\':
        return True#盘符
    return False#相对

def 会话文件地址(会话标识,路径):
    """编成 dsh-resource://file/session/<id>/<path>。"""
    规范化=路径.replace('\\','/')#统一斜杠
    while 规范化.startswith('./'):
        规范化=规范化[2:]#剥前导 ./
    return 'dsh-resource://file/session/'+编码段(会话标识)+'/'+编码路径(规范化)#会话作用域

def 文件资源地址(会话标识,cwd,路径):
    """相对或工作区内绝对走会话作用域；工作区外绝对仍写进同一会话地址。"""
    规范化=路径.replace('\\','/')#统一斜杠
    if not 是否绝对工作区路径(规范化):
        return 会话文件地址(会话标识,规范化)#相对
    根='' if cwd is None else cwd.replace('\\','/').rstrip('/')#工作区根
    if 根!='' and 规范化==根:
        return 会话文件地址(会话标识,'')#根本身
    if 根!='' and 规范化.startswith(根+'/'):
        return 会话文件地址(会话标识,规范化[len(根)+1:])#剥根
    return 会话文件地址(会话标识,规范化)#工作区外仍会话作用域

def 应用(上下文):
    """登记节点、词典、视图、统计、审批与详情。"""
    聊天源缓存={}#按绑定缓存（用 id 键近似 WeakMap）

    def 聊天源(绑定):
        """缺席空快照。"""
        键=id(绑定)#键
        if 键 in 聊天源缓存:#已有
            return 聊天源缓存[键]#返
        目标=上下文.uiConversation.binding(绑定).target('chat')#chat target
        def 取快照():
            """目标快照，缺则空。"""
            照=目标.getSnapshot()#快照
            return 照 if 照 is not None else 空聊天快照#缺则空
        def 订阅(监听):
            """订阅目标。"""
            return 目标.subscribe(监听)#订
        源={#可观察
            'getSnapshot':取快照,#快照
            'subscribe':订阅,#订阅
        }#源结束
        聊天源缓存[键]=源#缓存
        return 源#返

    登记会话节点(上下文)#会话节点
    def 解析聊天钩(绑定):
        """提供 chat 钩子。"""
        return {'hooks':{'chat':聊天源(绑定)}}#解析
    上下文.uiSession.provide({#提供 chat 钩子
        'hooks':['chat'],#钩子名
        'resolve':解析聊天钩,#解析
    })#provide 结束

    def 登记词典():
        """登记本包词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'ui-chat: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定
    聊天存储=创建聊天存储()#选中存储
    滚动位置={}#会话→滚动
    设置宿主=上下文.settingsScope.bind({'namespace':聊天设置命名空间})
    转录=转录视图策略(设置宿主)#呈现策略
    性能=性能用量策略(设置宿主)
    呈现=派生呈现策略(转录.mode)
    链接打开=创建快照存储(默认链接打开)
    def 采纳链接打开():
        快照=设置宿主.getSnapshot()
        段=快照['value'] if 快照 is not None and 'value' in 快照 else None
        if 段 is not None and 'linkOpening' in 段:
            链接打开.set(段['linkOpening'])
    设置宿主.subscribe(采纳链接打开)
    采纳链接打开()
    登记聊天节点渲染器(上下文,性能.模式,呈现)
    def 卸策略():
        def 拆除():
            转录.拆除()
            性能.拆除()
        return 拆除
    上下文.副作用(卸策略,'ui-chat: presentation policies')

    def 转录注入():
        """hooks + setTranscriptView。"""
        return {'hooks':{'transcriptView':转录.mode},'setTranscriptView':转录.setMode}#注入
    def 登记转录行():
        """呈现模式行。"""
        return 上下文.slots.register({#呈现模式行
            'name':'settings.general.item','id':'transcript-view','order':12,'locale':命名空间,
            'inject':转录注入,#注入
        },转录视图行)#登记
    上下文.slots.inject('settings.general.item',登记转录行)#挂

    def 视图注入():
        """返回卸除器。"""
        def 注入(会话标识,动作):
            """详情/文件/历史/滚动/分叉。"""
            绑定=上下文.sessions.binding(会话标识)#绑定
            if 绑定 is None:#未知
                raise 聊天错误('ui-chat: unknown session "'+str(会话标识)+'"')#抛
            会话=绑定.session#会话
            聊天=聊天源(绑定)#源
            仓动作=动作 if 动作 is not None else 聊天存储#动作
            def 打开详情(目标):
                """选定并打开。"""
                动作表=仓动作['actions'] if 'actions' in 仓动作 else None#动作表
                选=动作表['select'] if 动作表 is not None and 'select' in 动作表 else None#选
                if 选 is not None:#有
                    选(目标)#写
                上下文.layout.openDetails()#开
            def 存滚动(位置):
                """null 清除。"""
                if 位置 is None:
                    滚动位置.pop(会话标识,None)#删
                else:#记
                    滚动位置[会话标识]=位置#写
            def 读滚动():
                """当前滚动。"""
                return 滚动位置[会话标识] if 会话标识 in 滚动位置 else None#读
            def 取节点源(键):
                """nodes.source。存储为契约 dict。"""
                节点表=聊天['getSnapshot']()['nodes']#节点表
                return 节点表['source'](键)#节点
            def 取过程源(键):
                """nodes.processSource。存储为契约 dict。"""
                节点表=聊天['getSnapshot']()['nodes']#节点表
                return 节点表['processSource'](键)#节点
            def 关提及(属主):
                """fileMentions.forClosing(属主, 会话标识)。"""
                服务=上下文.获取服务('chatFileMentions')#服务
                if 服务 is None:#无
                    return None#无
                关=服务.forClosing#方法
                return 关(属主,会话标识)#提及
            def 打开文件(路径,选项=None):#打开文件
                """右侧边栏打开；行号作导航参数。"""
                列表=上下文.sessions.list.getSnapshot().byId#会话表
                摘要=列表[会话标识] if 会话标识 in 列表 else None#当前
                cwd=摘要['cwd'] if 摘要 is not None and 'cwd' in 摘要 else None#工作目录
                地址=文件资源地址(会话标识,cwd,路径)#会话作用域地址
                行=选项['line'] if 选项 is not None and 'line' in 选项 else None#行号
                if 行 is None:#无行号
                    上下文.sidebarRight.openResource(地址)#打开
                else:#带行号
                    上下文.sidebarRight.openResource(地址,{'params':{'line':行}})#打开并落点
            def 打开技能(名):#打开技能源
                """经输入触发打开技能引用。"""
                作用域=上下文.sessions.scope(会话标识)#会话作用域
                if 作用域 is None:#无
                    return#停
                触发=上下文.获取服务('inputTriggers')#触发服务
                if 触发 is None:#无
                    return#停
                触发.sessionOf(作用域).openReference('skill',{'ref':'/'+名})#打开技能引用
            def 打开外部链接(网址):#打开外部链接
                """优先侧栏浏览器标签，否则系统新窗。"""
                标签表=上下文.获取服务('sidebarRightTabs')#侧栏标签
                if 标签表 is not None and 标签表.get('browser') is not None and 链接打开.getSnapshot()=='sidebar':#侧栏浏览器
                    上下文.sidebarRight.openTab('browser',{'params':{'url':网址}})#侧栏打开
                else:#新窗
                    print('open external:',网址)#无浏览器或选择新窗时仅记日志
            def 加载更早():
                """会话 loadOlder。"""
                return 会话.loadOlder()#派
            def 加载到(序号):
                """会话 loadThrough。"""
                return 会话.loadThrough(序号)#派
            def 加载图(附件):
                """图 URL。"""
                return 上下文.uiConversation.imageUrl(会话标识,附件)#图
            def 分叉于(序号):
                """分叉并经工作区导航打开子会话。"""
                def 观察():
                    """后台分叉。"""
                    try:#成功
                        子标识=上下文.sessions.fork({'sessionId':会话标识,'atSeq':序号,'increaseTitle':True}).等待()#分叉
                        上下文.uiWorkspace.openSession(子标识)#经工作区打开
                    except BaseException:#失败
                        pass#源视图不变
                线=threading.Thread(target=观察)#线
                线.daemon=True#守护
                线.start()#启
            def 取组源(键):
                """grouped('chat').groupSource。"""
                会话面=上下文.uiConversation.binding(绑定)
                视=会话面.snapshot.getSnapshot()['views']
                分组=视['grouped']('chat') if 'grouped' in 视 else None
                if 分组 is None:
                    return None
                return 分组['groupSource'](键)
            return {#注入面
                'hooks':{'presentation':呈现},#呈现策略
                'keyedHooks':{#按键
                    'chatNode':取节点源,#节点
                    'chatNodeProcess':取过程源,#过程
                    'chatGroup':取组源,#过程组
                },#keyed 结束
                'openDetails':打开详情,#详情
                'fileMentions':关提及,#提及
                'openFile':打开文件,#打开文件
                'openSkill':打开技能,#打开技能
                'openExternalLink':打开外部链接,#外部链接
                'loadOlder':加载更早,#更早
                'loadThrough':加载到,#到 seq
                'loadImage':加载图,#图
                'chatScroll':{'save':存滚动,'read':读滚动},#滚动
                'forkAt':分叉于,#分叉
            }#返回
        def 聊天标签():
            """视图标签。"""
            return 翻译('view.chat')#标签
        return 上下文.slots.register({#登记 Chat 视图
            'name':'conversation.view','id':'chat','order':0,#视图
            'label':聊天标签,#标签
            'locale':命名空间,#文案
            'children':{#子
                'conversation.chat.node':{'kind':'keyed','scope':'session','inject':聊天节点注入},#节点
                'conversation.message.images':{'kind':'single','scope':'session'},#图片
            },#children 结束
            'store':聊天存储,#store
            'inject':注入,#注入
        },聊天视图)#组件
    上下文.slots.inject('conversation.view',视图注入)#挂视图

    def 登记统计():
        """统计停靠。"""
        return 上下文.slots.register({#统计停靠
            'name':'conversation.composer.dock','id':'stats','order':0,'locale':命名空间,#统计
            'inject':lambda:{'hooks':{'performanceUsage':性能.模式}},
        },统计行)#登记
    上下文.slots.inject('conversation.composer.dock',登记统计)#挂

    def 登记审批():
        """审批详情。"""
        return 上下文.slots.register({#审批详情
            'name':'conversation.approval.detail',#槽
        },审批命令)#登记
    上下文.slots.inject('conversation.approval.detail',登记审批)#挂

    def 关详情():
        """关闭详情栏。"""
        return 上下文.layout.closeDetails()#关
    def 详情注入():
        """详情关闭。"""
        return {'closeDetails':关详情}#关闭
    def 登记详情():
        """详情面板。"""
        return 上下文.slots.register({#详情面板
            'name':'details','locale':命名空间,#详情
            'children':{'conversation.details.tool':{'kind':'single','scope':'session'}},#工具子
            'store':聊天存储,#store
            'inject':详情注入,#关闭
        },详情面板)#登记
    上下文.slots.inject('details',登记详情)#挂

inject=依赖#Cordis 依赖声明
apply=应用#Cordis 插件入口
