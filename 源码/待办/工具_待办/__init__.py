"""面向模型的整表替换待办工具。

每次调用向所属智能体会话追加 `todo/write` 快照；回放后写覆盖，界面从会话事件渲染。非智能体调用方没有所属列表，直接拒绝。

对齐上游 `@deepseek-ai/dsh-tool-todo`。公开面仅中文名。配置键、事件名与诊断英文字面量保持上游。本包不提供默认导出（Loader 的 unwrapExports 会折叠掉 inject）。
"""
import json#重复内容报错片段
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 路径上节点,布尔字段#配置字段
已兑现=cordis.工具.已兑现#操作链承诺
是否thenable=cordis.工具.是否thenable#可等待判定
from ...内核.工具 import 定义工具#定义面向模型的工具
from .类型 import 待办条目,待办状态#再导出类型面

__all__=['名称','注入','配置','应用','待办条目','待办状态']#仅中文公开名

名称='tool-todo'#Cordis插件名（字面量）
注入=['tools']#依赖工具服务
描述头='Record and update a structured task list for the current work. Send the ENTIRE list every call — it REPLACES the previous list (there are no partial updates, no per-item edits). Use it to plan multi-step work and show progress: add one todo per concrete step before you start. '#描述前段，字面量不翻译
描述并行='Mark every todo being actively worked on `in_progress` — several at once when work genuinely runs in parallel (e.g. concurrent subagents or background commands), one for sequential work; while work remains, at least one task should be `in_progress`. '#并行政策句
描述单活='Keep AT MOST ONE todo `in_progress` at a time; while work remains, exactly one active task should be `in_progress`. '#单活政策句
描述尾='Mark a todo `completed` the moment it is done (do not batch completions), and allow no `in_progress` item only once all work is complete. Skip the list for trivial single-step tasks. Statuses: `pending` (not started), `in_progress` (being worked on now), `completed` (finished).'#描述后段
配置=路径上节点({#待办工具部署配置
    'allowParallelInProgress':布尔字段(可空=False),#是否允许多条 in_progress
})#配置模式结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 描述(允许并行):#按政策拼工具描述
    """一次激活面向模型的描述。只有活跃状态那句随并行政策变化。"""
    if 允许并行:#允许多条 in_progress
        中段=描述并行#并行句
    else:#单活纪律
        中段=描述单活#单活句
    return 描述头+中段+描述尾#三段拼接

def 转待办列表(原始,允许并行):#校验并收成规范列表
    """校验参数模式表达不了的值约束，收成规范待办列表：修剪后非空且唯一的 content；未开并行时至多一条 in_progress。"""
    待办们=[]#规范列表
    已见=set()#已见内容
    活跃=0#in_progress 条数
    for 条目 in 原始:#逐条
        内容=取字段(条目,'content').strip()#修剪
        if len(内容)==0:#空内容
            raise Exception('invalid todo: `content` must be a non-empty string')#空内容非法
        if 内容 in 已见:#重复
            raise Exception('invalid todos: duplicate content '+json.dumps(内容,ensure_ascii=False))#重复内容
        已见.add(内容)#记下
        状态=取字段(条目,'status')#生命周期
        if 状态=='in_progress':#正在做
            活跃+=1#计数
        待办们.append(待办条目(内容,状态))#收下规范条
    if (not 允许并行) and 活跃>1:#单活却标了多条
        raise Exception('invalid todos: at most one task may be in_progress (got '+str(活跃)+')')#拒绝
    return 待办们#规范列表

def 待办投影模式():#todos 投影的线上模式
    """整表或首次写入前的 null。会话投影缝尚未迁完时仍按同一形状登记。"""
    return {#联合模式
        'anyOf':[#数组或空
            {#整表
                'type':'array',#数组
                'items':{#条目
                    'type':'object',#对象
                    'additionalProperties':False,#禁止额外字段
                    'properties':{#字段
                        'content':{'type':'string'},#文案
                        'status':{'type':'string','enum':list(待办状态)},#三态
                    },#字段结束
                },#条目结束
            },#整表结束
            {'type':'null'},#尚未写入
        ],#联合结束
    }#模式结束

def 应用(上下文,配置值):#注册工具与可选投影单元
    """在 ctx.tools 上登记 todo_write；组合了会话投影缝时再登记 todos 单元。"""
    允许并行=取字段(配置值,'allowParallelInProgress')#部署政策
    def 投影安装(投影上下文,*剩余):#有投影注册表才激活
        """单元子插件只在投影注册表被组合时激活。折叠：最新整表，下一 turn/start 清空。"""
        def 初始():#首次状态
            """首次写入前为 null。"""
            return None#尚未写入
        def 折叠(状态,事件):#按事件折叠
            """最新整表；turn/start 清空；其余保持同一引用。"""
            种类=取字段(事件,'type')#事件类型
            if 种类=='todo/write':#整表替换
                return 取字段(取字段(事件,'data'),'todos')#后写覆盖
            if 种类=='turn/start':#新轮次
                return None#清空清单
            return 状态#保持
        def 视图(状态):#对外视图
            """视图即状态本身。"""
            return 状态#原样
        投影上下文.sessionProjections.register({
            'key':'todos',#投影键
            'schema':待办投影模式(),#线上模式
            'init':初始,#初始
            'apply':折叠,#折叠
            'view':视图,#视图
            'stateVersion':2,#状态版本
        })#登记结束
    上下文.inject(['sessionProjections'],投影安装)#等到投影缝
    def 渲染(参数,值):#模型看到计数摘要
        """把结构化结果渲染成一条计数文本。"""
        计数=取字段(值,'counts')#三态计数
        文本='Updated todo list: '+str(取字段(计数,'pending'))+' pending, '+str(取字段(计数,'inProgress'))+' in progress, '+str(取字段(计数,'completed'))+' completed.'#摘要
        return [{'type':'text','text':文本}]#单个文本块
    def 执行(参数,执行上下文):#整表替换
        """校验后写入所属智能体会话。"""
        待办们=转待办列表(取字段(参数,'todos'),允许并行)#规范列表
        智能体=取字段(执行上下文,'agent')#调用方智能体
        if 智能体 is None:#非智能体调用方
            raise Exception('todo_write requires an owning agent session')#拒绝而不是静默空操作
        解开(智能体.session.append('todo/write',{'todos':待办们}))#追加整表快照
        def 计数(状态):#按状态计数
            """数某一状态的条数。"""
            数=0#计数
            for 条 in 待办们:#逐条
                if 取字段(条,'status')==状态:#命中
                    数+=1#加一
            return 数#条数
        投影=[]#回给模型的列表
        for 条 in 待办们:#逐条拷贝
            投影.append({'content':取字段(条,'content'),'status':取字段(条,'status')})#字段拷贝
        return 已兑现({#结构化结果
            'todos':投影,#整表
            'counts':{#三态计数
                'pending':计数('pending'),#未开始
                'inProgress':计数('in_progress'),#进行中
                'completed':计数('completed'),#已完成
            },#计数结束
        })#兑现结束
    def 呈现调用(参数):#UI卡片
        """调用时通用卡片。"""
        return {#通用卡片
            'card':'generic',#通用卡片
            'title':'Update todo list',#标题
            'kind':'other',#其它种类
            'rawInput':取字段(参数,'todos'),#原始输入
        }#卡片结束
    待办工具=定义工具({#面向模型的 todo_write
        'name':'todo_write',#工具名
        'description':描述(允许并行),#按政策拼描述
        'parameters':{#参数模式
            'todos':{#整表
                'type':'array',#数组
                'required':True,#必填
                'description':'The COMPLETE task list, replacing any previous list.',#整表替换
                'items':{#条目
                    'type':'object',#对象
                    'additionalProperties':False,#禁止额外字段
                    'properties':{#字段
                        'content':{'type':'string','required':True,'description':'What the task is — a short imperative line.'},#文案
                        'status':{#生命周期
                            'type':'string',#字符串
                            'required':True,#必填
                            'enum':list(待办状态),#三态
                            'description':'pending (not started) | in_progress (now) | completed (done).',#三态说明
                        },#状态结束
                    },#字段结束
                },#条目结束
            },#todos结束
        },#参数结束
        'output':{#结构化输出加渲染
            'schema':{#输出JSON模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'todos':{#回写整表
                        'type':'array',#数组
                        'required':True,#必填
                        'items':{#条目
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#字段
                                'content':{'type':'string','required':True},#文案
                                'status':{'type':'string','required':True,'enum':list(待办状态)},#三态
                            },#字段结束
                        },#条目结束
                    },#todos结束
                    'counts':{#三态计数
                        'type':'object',#对象
                        'additionalProperties':False,#禁止额外字段
                        'required':True,#必填
                        'properties':{#字段
                            'pending':{'type':'integer','required':True},#未开始
                            'inProgress':{'type':'integer','required':True},#进行中
                            'completed':{'type':'integer','required':True},#已完成
                        },#字段结束
                    },#counts结束
                },#字段结束
            },#schema结束
            'render':渲染,#计数摘要
        },#output结束
        'execute':执行,#整表替换
        'presentCall':呈现调用,#UI卡片
    })#定义结束
    上下文.tools.登记(待办工具)#挂到工具注册表
