"""登记 Chat Conversation target、渲染器、统计与详情面。

对齐上游 `ui-chat/src/client/apply.ts`。公开面仅中文名。
"""
from ..聊天设置 import 聊天设置命名空间#Chat 设置段
from .文案 import 命名空间,中文,英文#词典
from .仓库 import 创建聊天仓库#选中 store
from .转录视图 import 转录视图策略#呈现策略
from .约定.快照 import 空聊天快照#空快照
from .聊天.用回合数据 import 用回合数据值#回合数据
from .聊天.登记节点渲染器 import 登记聊天节点渲染器#节点渲染器
from .聊天.聊天视图 import 聊天视图#Chat 视图
from .聊天.统计行 import 统计行#统计
from .聊天.审批命令 import 审批命令#审批卡
from .详情.详情面板 import 详情面板#详情
from .设置.转录视图行 import 转录视图行#设置行
from .会话节点 import 登记会话节点#会话节点

__all__=['注入','应用']#仅中文公开名

注入=[#前置 inject
    'slots','sessions','uiSession','uiConversation','layout','locale',
    'settingsScope','remote','remote.session',
]#依赖

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

聊天节点注入={#CHAT_NODE_INJECT
    'hooks':{#钩子
        'turnData':lambda _标准,数据: (lambda 键:用回合数据值(数据,键)),#回合数据
    },#hooks 结束
}#注入结束

def 应用(上下文):#挂载 Chat 拥有的全部贡献
    """登记节点、词典、视图、统计、审批与详情。"""
    聊天源缓存={}#按绑定缓存（用 id 键近似 WeakMap）

    def 聊天源(绑定):#取或建 Chat 快照源
        """缺席空快照。"""
        键=id(绑定)#键
        if 键 in 聊天源缓存:#已有
            return 聊天源缓存[键]#返
        目标=上下文.uiConversation.binding(绑定).target('chat')#chat target
        源={#可观察
            'getSnapshot':lambda:目标.getSnapshot() if 目标.getSnapshot() is not None else 空聊天快照,#快照
            'subscribe':lambda 监听:目标.subscribe(监听),#订阅
        }#源结束
        聊天源缓存[键]=源#缓存
        return 源#返

    登记会话节点(上下文)#会话节点
    登记聊天节点渲染器(上下文)#渲染器
    if hasattr(上下文,'uiSession') and hasattr(上下文.uiSession,'provide'):#有 provide
        上下文.uiSession.provide({#提供 chat 钩子
            'hooks':['chat'],#钩子名
            'resolve':lambda 绑定:{'hooks':{'chat':聊天源(绑定)}},#解析
        })#provide 结束

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-chat: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定
    聊天仓=创建聊天仓库()#选中 store
    滚动位置={}#会话→滚动
    转录=转录视图策略(上下文.settingsScope.bind({'namespace':聊天设置命名空间}))#呈现策略

    def 转录注入():#设置行注入
        """hooks + setTranscriptView。"""
        return {'hooks':{'transcriptView':转录.mode},'setTranscriptView':转录.setMode}#注入
    上下文.slots.inject('settings.general.item',lambda:上下文.slots.register({#呈现模式行
        'name':'settings.general.item','id':'transcript-view','order':12,'locale':命名空间,
        'inject':转录注入,#注入
    },转录视图行))#登记

    def 视图注入():#Chat 视图登记
        """返回卸除器。"""
        def 注入(会话标识,动作):#视图注入面
            """详情/文件/历史/滚动/分叉。"""
            绑定=上下文.sessions.binding(会话标识)#绑定
            if 绑定 is None:#未知
                raise Exception('ui-chat: unknown session "'+str(会话标识)+'"')#抛
            会话=取字段(绑定,'session')#会话
            聊天=聊天源(绑定)#源
            仓动作=动作 if 动作 is not None else 聊天仓#动作
            def 打开详情(目标):#打开详情
                """选定并打开。"""
                选=取字段(仓动作,'select') or (仓动作.get('actions',{}) or {}).get('select')#选
                if callable(选):#有
                    选(目标)#写
                上下文.layout.openDetails()#开
            def 存滚动(位置):#保存滚动
                """null 清除。"""
                if 位置 is None:#清
                    滚动位置.pop(会话标识,None)#删
                else:#记
                    滚动位置[会话标识]=位置#写
            return {#注入面
                'hooks':{'transcriptView':转录.mode},#呈现
                'keyedHooks':{#按键
                    'chatNode':lambda 键:聊天['getSnapshot']()['nodes'].source(键) if hasattr(聊天['getSnapshot']()['nodes'],'source') else None,#节点
                    'chatNodeProcess':lambda 键:聊天['getSnapshot']()['nodes'].processSource(键) if hasattr(聊天['getSnapshot']()['nodes'],'processSource') else None,#过程
                },#keyed 结束
                'openDetails':打开详情,#详情
                'fileMentions':lambda 属主:(取字段(上下文.get('chatFileMentions'),'forClosing')(属主) if 上下文.get('chatFileMentions') else None),#提及
                'openFile':lambda 路径:None,#打开文件（远程异步略）
                'loadOlder':lambda:取字段(会话,'loadOlder')() if callable(取字段(会话,'loadOlder')) else None,#更早
                'loadThrough':lambda 序号:取字段(会话,'loadThrough')(序号) if callable(取字段(会话,'loadThrough')) else None,#到 seq
                'loadImage':lambda 附件:上下文.uiConversation.imageUrl(会话标识,附件),#图
                'chatScroll':{'save':存滚动,'read':lambda:滚动位置.get(会话标识)},#滚动
                'forkAt':lambda 序号:None,#分叉（异步略）
            }#返回
        return 上下文.slots.register({#登记 Chat 视图
            'name':'conversation.view','id':'chat','order':0,#视图
            'label':lambda:翻译('view.chat'),#标签
            'locale':命名空间,#文案
            'children':{#子
                'conversation.chat.node':{'kind':'keyed','scope':'session','inject':聊天节点注入},#节点
                'conversation.message.images':{'kind':'single','scope':'session'},#图片
            },#children 结束
            'store':聊天仓,#store
            'inject':注入,#注入
        },聊天视图)#组件
    上下文.slots.inject('conversation.view',视图注入)#挂视图

    上下文.slots.inject('conversation.composer.dock',lambda:上下文.slots.register({#统计停靠
        'name':'conversation.composer.dock','id':'stats','order':0,'locale':命名空间,#统计
    },统计行))#登记

    上下文.slots.inject('conversation.approval.detail',lambda:上下文.slots.register({#审批详情
        'name':'conversation.approval.detail',#槽
    },审批命令))#登记

    上下文.slots.inject('details',lambda:上下文.slots.register({#详情面板
        'name':'details','locale':命名空间,#详情
        'children':{'conversation.details.tool':{'kind':'single','scope':'session'}},#工具子
        'store':聊天仓,#store
        'inject':lambda:({'closeDetails':lambda:上下文.layout.closeDetails()}),#关闭
    },详情面板))#登记
