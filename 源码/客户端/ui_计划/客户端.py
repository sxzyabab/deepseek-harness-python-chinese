from uuid import uuid4 as 随机UUID#审阅窗身份
from .文案 import 命名空间,中文,英文#词表
from .计划芯片 import 计划芯片#芯片组件
from .计划定义 import 计划定义#对话定义
from .计划资源 import 计划资源提供者#资源
from .计划 import 计划地址,解析计划地址#地址
from .审阅预览 import 审阅预览地址,是否审阅预览地址#审阅
from .审阅存储 import 创建计划审阅存储#审阅 store
from .失败行 import 计划失败行#失败行
from .计划卡 import 计划卡,计划审阅打开#卡与审阅打开
from .计划预览 import 计划预览,计划标题#预览与标题

__all__=[#仅中文公开名
    '依赖','应用','计划芯片','命名空间','中文','英文',
    '计划定义','计划资源提供者','计划地址','解析计划地址',
    '审阅预览地址','是否审阅预览地址','创建计划审阅存储','计划失败行',
    '计划卡','计划审阅打开','计划预览','计划标题',
]

依赖=['slots','remote','remote.commands','remote.session','sessions','locale','uiConversation','resources','sidebarRight','sidebarRightTabs']#依赖
预览标识='@deepseek-ai/dsh-client-ui-plan'#侧栏类型 id

def 应用(上下文):#安装计划控制浏览器半边
    """登记计划控制、永久 Chat 卡与侧栏文档阅读。"""
    def 登记词表():#登记中英文案
        """把计划命名空间写进 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记词表
    上下文.副作用(登记词表,'ui-plan: dictionaries')#登记词表
    翻译=上下文.locale.bind(命名空间)#文案

    def 登记定义():#对话定义
        """登记 submitted-plan。"""
        return 上下文.uiConversation.events.register(计划定义)#登记
    上下文.副作用(登记定义,'ui-plan: conversation definition')#定义

    def 登记资源():#资源
        """登记 plan 协议。"""
        return 上下文.resources.register(计划资源提供者(上下文.remote.session))#登记
    上下文.副作用(登记资源,'ui-plan: resources')#资源

    def 可打开(地址):#侧栏可否打开
        """计划或审阅预览。"""
        return 解析计划地址(地址) is not None or 是否审阅预览地址(地址)#可
    def 预览标题():#侧栏标题
        """文案。"""
        return 翻译('preview.title')#标题
    def 登记侧栏类型():#侧栏类型
        """登记 plan 标签种。"""
        return 上下文.sidebarRightTabs.register({#登记
            'id':预览标识,'kind':'plan',#身份
            'patterns':['dsh-resource://plan/**','dsh-resource://plan-review/**'],#模式
            'priority':'builtin','canOpen':可打开,'title':预览标题,#元数据
        })#登记
    上下文.副作用(登记侧栏类型,'ui-plan: sidebar type')#侧栏

    def 打开计划面(会话标识):#打开计划注入
        """按调用打开侧栏计划。"""
        def 打开计划(调用标识):#打开
            """编码地址并打开。"""
            子=上下文.sessions.subagentAddress(会话标识)#子智能体
            if 子 is None:#普通
                会话={'kind':'session','sessionId':会话标识}#会话
            else:#子智能体
                会话=dict(子)#拷贝
                会话['kind']='subagent'#种
            上下文.sidebarRight.openResourceIn(会话标识,计划地址({'session':会话,'callId':调用标识}))#打开
        return {'openPlan':打开计划}#注入

    审阅窗=str(随机UUID())#审阅窗
    审阅存储=创建计划审阅存储()#store

    def 登记回合尾():#回合尾卡
        """登记计划卡。"""
        return 上下文.slots.register({#登记
            'name':'conversation.chat.turnTail','id':预览标识,'locale':命名空间,#元数据
            'inject':打开计划面,#注入
        },计划卡)#计划卡
    上下文.slots.inject('conversation.chat.turnTail',登记回合尾)#挂

    def 审阅注入(会话标识):#审阅动作注入
        """打开审阅或临时预览。"""
        def 打开审阅(审阅,请求键):#打开
            """有 callId 开计划，否则临时预览。"""
            if 'callId' in 审阅 and 审阅['callId'] is not None:#有调用
                打开计划面(会话标识)['openPlan'](审阅['callId'])#开计划
                return#停
            正文=审阅['plan'] if 'plan' in 审阅 else ''#正文
            标题=正文.strip().split('\n')[0].lstrip('#').strip() if 正文!='' else ''#首行标题
            上下文.sidebarRight.openResourceIn(会话标识,审阅预览地址(会话标识,审阅窗+':'+请求键),{#临时
                'params':{'planReview':{'markdown':正文,'title':标题}},#参数
            })#打开
        return {'openReview':打开审阅}#注入

    def 登记审阅动作():#审阅动作
        """登记审阅打开。"""
        return 上下文.slots.register({#登记
            'name':'conversation.plan-review.actions','id':预览标识,#元数据
            'locale':命名空间,'store':审阅存储,'inject':审阅注入,#注入
        },计划审阅打开)#审阅打开
    上下文.slots.inject('conversation.plan-review.actions',登记审阅动作)#挂

    def 登记预览标签():#侧栏预览
        """登记计划预览标签。"""
        return 上下文.slots.register({#登记
            'name':'sidebar.right.pane.tab','key':预览标识,'locale':命名空间,#元数据
        },计划预览)#预览
    上下文.slots.inject('sidebar.right.pane.tab',登记预览标签)#挂

    def 登记预览标题():#侧栏标题
        """登记计划标题。"""
        return 上下文.slots.register({#登记
            'name':'sidebar.right.pane.tab.title','key':预览标识,#元数据
        },计划标题)#标题
    上下文.slots.inject('sidebar.right.pane.tab.title',登记预览标题)#挂

    def 注入面(会话标识):#按会话解析计划芯片注入面
        """执行 /plan off 离开计划模式。"""
        def 退出计划模式():#执行 /plan off
            """受理执行时为 None；否则是用户可见失败行。"""
            结果=上下文.remote.commands.execute(会话标识,'/plan off',[]).等待()#执行
            if not 结果['ok']:#命令失败
                错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
                消息=错误['message'] if 'message' in 错误 else None#文案
                码=错误['code'] if 'code' in 错误 else None#错误码
                return str(消息)+' ('+str(码)+')'#失败行
            if 'value' not in 结果 or 结果['value'] is None:#宿主无该命令
                return 'unknown command: /plan off'#失败行
            return None#受理
        return {'exitPlanMode':退出计划模式}#注入面

    def 登记芯片():#等席位出现
        """登记计划芯片。"""
        return 上下文.slots.register({#席位登记
            'name':'conversation.input.plan',#席位槽名
            'locale':命名空间,#文案
            'inject':注入面,#注入
        },计划芯片)#计划芯片
    上下文.slots.inject('conversation.input.plan',登记芯片)#等席位出现

inject=依赖#框架槽
apply=应用#框架槽
