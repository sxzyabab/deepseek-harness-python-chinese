"""子智能体引用插件的浏览器半边：登记「@」源、目录动作与只读编写器。

对齐上游 `ui-subagent/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文,子智能体文案键#词典
from .只读认领 import 选择只读子智能体#认领判定
from .只读撰写器 import 只读撰写器,样式表 as 只读样式表#只读面
from .目录动作 import (#目录动作
    目录动作,格式化令牌,格式化时长,格式化精确时长,令牌合计,活动时长毫秒,样式表 as 目录样式表,
)#目录导出

__all__=[#仅中文公开名
    '注入','应用','命名空间','中文','英文','子智能体文案键',
    '选择只读子智能体','只读撰写器','目录动作',
    '格式化令牌','格式化时长','格式化精确时长','令牌合计','活动时长毫秒',
    '只读样式表','目录样式表',
]#公开面结束

注入=['inputTriggers','sessions','slots','locale']#触发源、会话、槽位、文案

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 应用(上下文):#安装浏览器半边
    """登记词典、「@」源、目录按钮与只读编写器。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-subagent: dictionaries')#词典
    会话服务=上下文.sessions#会话服务

    def 子标签(会话,查询):#从列表快照滤子标题
        """本会话正在运行且标题含查询的子项展示标题。"""
        快照=会话服务.list.getSnapshot()#列表快照
        表=取字段(快照,'byId') or {}#byId
        结果=[]#标题
        for 子 in (表.values() if hasattr(表,'values') else []):#逐条
            if 取字段(子,'parentId')==取字段(会话,'sessionId') and 取字段(子,'running') and 查询 in (取字段(子,'displayTitle') or ''):#命中
                结果.append(取字段(子,'displayTitle'))#标题
        return 结果#列表

    源={#「@」子智能体触发源
        'trigger':'@',#触发
        'name':'subagent',#名
        'candidates':lambda 会话,选项:[{'name':名} for 名 in 子标签(会话,取字段(选项,'query',''))],#候选
        'lexicon':lambda 会话:子标签(会话,''),#词表
        'subscribeLexicon':lambda _会话,监听:会话服务.list.subscribe(监听),#订阅
        'onPick':lambda 载荷:{'text':'@'+取字段(取字段(载荷,'candidate'),'name')+' '},#选定
        'codec':{#编解码
            'clipboardText':lambda 引用:'@'+引用,#剪贴板
            'serialize':lambda 引用:'@'+引用,#序列化
        },#编解码结束
    }#源结束
    触发=上下文.get('inputTriggers')#触发服务
    上下文.effect(lambda:触发.registerSource(源),'ui-subagent: @ source')#登记源

    def 目录注入(_父会话标识=None):#目录注入面
        """打开子项、刷新、记下开合。"""
        return {#注入
            'openChild':lambda 地址:会话服务.openSubagent(地址),#打开
            'refresh':lambda 父:会话服务.refreshSubagents(父),#刷新
            'setCatalogOpen':lambda 父,开:会话服务.setSubagentCatalogOpen(父,开),#开合
        }#结束

    上下文.slots.inject('conversation.session.header.actions',lambda:上下文.slots.register({#目录按钮
        'name':'conversation.session.header.actions',#槽
        'id':'subagent-catalog',#id
        'order':10,#序
        'locale':命名空间,#文案
        'inject':目录注入,#注入
    },目录动作))#组件

    上下文.slots.inject('conversation.composer',lambda:上下文.slots.register({#只读编写器
        'name':'conversation.composer',#槽
        'priority':-10,#负优先
        'locale':命名空间,#文案
        'select':选择只读子智能体,#选择器
    },只读撰写器))#组件
