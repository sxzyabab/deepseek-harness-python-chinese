"""登记 Chat Conversation target、渲染器、统计与详情面。

对齐上游 `ui-chat/src/client/apply.ts`。公开面仅中文名。
"""
import 客户端.ui_侧边栏_文档预览.客户端 as _侧边栏文档预览#文档预览面：SidebarRightResourceParamsMap.file
from ..聊天设置 import 聊天设置命名空间#Chat 设置段
from .文案 import 命名空间,中文,英文#词典
from .存储 import 创建聊天存储#选中存储
from .转录视图 import 转录视图策略#呈现策略
from .约定.快照 import 空聊天快照#空快照
from .聊天.用回合数据 import 用回合数据值#回合数据
from .聊天.登记节点渲染器 import 登记聊天节点渲染器#节点渲染器
from .聊天.聊天视图 import 聊天视图#Chat 视图
from .聊天.统计行 import 统计行#统计（对齐 StatsPills）
from .聊天.审批命令 import 审批命令#审批卡
from .详情.详情面板 import 详情面板#详情
from .设置.转录视图行 import 转录视图行#设置行
from .会话节点 import 登记会话节点#会话节点
from .会话节点.节点工厂 import 聊天错误#本包异常

_=_侧边栏文档预览#保活侧效导入（对齐 documentpreview，非 textpreview）

__all__=['注入','应用']#仅中文公开名

注入=[#前置 inject
    'slots','sessions','uiSession','uiConversation','layout','locale',
    'settingsScope','remote','remote.session',
]#依赖

def 造回合数据(_标准,数据):
    """按节点读回合数据。"""
    def 读键(键):
        """读一键。"""
        return 用回合数据值(数据,键)#值
    return 读键#工厂

聊天节点注入={#CHAT_NODE_INJECT
    'hooks':{#钩子
        'turnData':造回合数据,#回合数据
    },#hooks 结束
}#注入结束

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
    登记聊天节点渲染器(上下文)#渲染器
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
    转录=转录视图策略(上下文.settingsScope.bind({'namespace':聊天设置命名空间}))#呈现策略

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
            会话=绑定.session#会话对象
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
                if 位置 is None:#清
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
            def 打开文件(_路径):
                """打开文件（远程异步略）。"""
                return None#略
            def 加载更早():
                """会话 loadOlder。"""
                return 会话.loadOlder()#派
            def 加载到(序号):
                """会话 loadThrough。"""
                return 会话.loadThrough(序号)#派
            def 加载图(附件):
                """图 URL。"""
                return 上下文.uiConversation.imageUrl(会话标识,附件)#图
            def 分叉于(_序号):
                """分叉（异步略）。"""
                return None#略
            return {#注入面
                'hooks':{'transcriptView':转录.mode},#呈现
                'keyedHooks':{#按键
                    'chatNode':取节点源,#节点
                    'chatNodeProcess':取过程源,#过程
                },#keyed 结束
                'openDetails':打开详情,#详情
                'fileMentions':关提及,#提及
                'openFile':打开文件,#打开文件
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

inject=注入#Cordis 依赖声明
apply=应用#Cordis 插件入口
