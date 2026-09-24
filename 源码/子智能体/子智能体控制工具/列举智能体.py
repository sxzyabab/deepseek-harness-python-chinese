from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from ...内核.工具 import 定义工具#导入工具定义
from ...模型后端.llm import 断言永不#导入穷尽检查
from ..子智能体.错误 import 子智能体错误#缝内失败

名称='tool-subagent-list-agents'#Cordis插件名
依赖=['tools','subagents','agents']#依赖工具、子智能体与智能体注册表

列举智能体作用域=Literal['children','descendants']#列举作用域

class 列举智能体请求(TypedDict):#模型请求
    scope:NotRequired[列举智能体作用域]#可选作用域

class 列举智能体规格(TypedDict):#内部必填规格
    scope:列举智能体作用域#已解析作用域

class 列举智能体子体行(TypedDict):#子体行
    kind:Literal['child']#子体
    id:str#会话id
    label:str#标签
    status:Literal['running','inactive']#活注册表状态
    parent:NotRequired[str]#可选父id
    depth:NotRequired[int]#可选深度

class 列举智能体诊断行(TypedDict):#诊断行
    kind:Literal['diagnostic']#诊断
    id:str#会话id
    reason:Literal['corrupt','unsupported','unavailable']#诊断原因
    parent:NotRequired[str]#可选父id
    depth:NotRequired[int]#可选深度

列举智能体条目=列举智能体子体行|列举智能体诊断行#面向模型的条目

__all__=[#仅中文公开名
    '名称','依赖','应用',
    '列举智能体作用域','列举智能体请求','列举智能体规格',
    '列举智能体子体行','列举智能体诊断行','列举智能体条目',
    '解析列举智能体请求','状态于','投影',
]

def 解析列举智能体请求(请求):
    """把可选模型请求解析成内部必填作用域规格；缺省 scope 为 `children`。请求为 dict。"""
    if 请求 is None or 'scope' not in 请求 or 请求['scope'] is None:#未给出
        return {'scope':'children'}#默认直接子
    return {'scope':请求['scope']}#已解析规格

def 状态于(智能体服务,标识):
    """经活 Agent 注册表报告回合活动：正在跑为 `running`，否则 `inactive`。"""
    智能体=智能体服务.获取(标识)#活智能体
    if 智能体 is not None and 智能体.status=='running':#活动驱动
        return 'running'#正在工作
    return 'inactive'#未在跑

def 投影(智能体服务,条目,位置=None):
    """把一行服务条目投影成面向模型的条目，或省略一次性子体。条目与位置为 dict。"""
    if 位置 is None:#无树位置
        处={}#空位置
    else:#有树位置
        处={'parent':位置['parentId'],'depth':位置['depth']}#位置字段
    if 条目['kind']=='diagnostic':#诊断行原样带位置
        行={'kind':'diagnostic','id':条目['id'],'reason':条目['reason']}#诊断基行
        行.update(处)#并入位置
        return 行#诊断
    if 条目['mode']!='continuable':#非可续跑
        return None#省略一次性
    行={#可续跑子体行
        'kind':'child',#子体
        'id':条目['id'],#会话id
        'label':条目['label'],#标签
        'status':状态于(智能体服务,条目['id']),#活状态
    }#基行
    行.update(处)#并入可选位置
    return 行#子体行

def 应用(上下文):
    """登记 `list_agents` 工具。"""
    def 渲染列表(参数,条目列表):
        """按作用域渲染列表文本块；空列表渲染 `(no subagents)`。参数与条目为 dict。"""
        请求=解析列举智能体请求(参数)#解析作用域
        if len(条目列表)==0:#空列表
            正文='(no subagents)'#空文案
        else:#有条目
            行列表=[]#收集行文案
            for 条目 in 条目列表:#逐行
                if 请求['scope']=='descendants':#后代才带位置
                    处=' parent='+str(条目['parent'] if 'parent' in 条目 else None)+' depth='+str(条目['depth'] if 'depth' in 条目 else None)#位置文案
                else:#直接子
                    处=''#无位置
                if 条目['kind']=='child':#子体行
                    行列表.append(str(条目['id'])+' ['+str(条目['status'])+']'+处+' — '+str(条目['label']))#子体行
                else:#诊断行
                    行列表.append(str(条目['id'])+' [diagnostic: '+str(条目['reason'])+']'+处)#诊断行
            正文='\n'.join(行列表)#换行拼接
        return [{'type':'text','text':正文}]#文本块
    def 执行列举(参数,执行元数据):
        """按作用域列举可续跑子体或后代树，并投影为面向模型的条目。参数与执行为 dict；父为智能体对象。"""
        if 'agent' not in 执行元数据 or 执行元数据['agent'] is None:#无智能体调用方
            raise 子智能体错误('list_agents requires a calling agent (exec.agent was undefined)','NO_AGENT')#拒绝
        父=执行元数据['agent']#调用方智能体
        请求=解析列举智能体请求(参数)#解析作用域
        作用域=请求['scope']#已解析作用域
        信号=执行元数据['signal'] if 'signal' in 执行元数据 else None#取消信号
        if 作用域=='children':#直接子
            条目列表=上下文.subagents.列出子体(父.id,信号)#列举直接子
            结果=[]#投影结果
            for 条目 in 条目列表:#逐条投影
                投影行=投影(上下文.agents,条目)#投影
                if 投影行 is not None:#非省略
                    结果.append(投影行)#收下
            return 结果#返回投影
        if 作用域=='descendants':#整棵树
            条目列表=上下文.subagents.列出后代(父.id,信号)#列举后代
            结果=[]#投影结果
            for 条目 in 条目列表:#逐条投影
                投影行=投影(上下文.agents,条目,条目)#带位置投影
                if 投影行 is not None:#非省略
                    结果.append(投影行)#收下
            return 结果#返回投影
        return 断言永不(作用域,'list_agents scope')#不可达
    上下文.tools.登记(定义工具({#登记 list_agents
        'name':'list_agents',#工具名
        'description':(#工具描述
            'List your continuable background subagents by durable id and label. Use it to recall which ones '
            +'you started, not to poll for completion — you are told when one finishes. Status comes from the live '
            +'registry: running means the agent is working right now; inactive means no turn is executing, whether '
            +'the child is loaded or must be resumed. inactive does not describe task completion, success, failure, '
            +'or waiting for other agents. A `send_message` steers a running child at its nearest step boundary '
            +'or starts or resumes a turn for an inactive child, and a direct child remains a `send_message` '
            +'candidate in every status. The snapshot is not a delivery '
            +'promise — `send_message` performs the authoritative check and may still fail. Children that could '
            +'not be read are reported as diagnostics only in `descendants` scope. Scope `descendants` '
            +'walks the whole tree below you in stable pre-order, annotating each entry with its durable direct-parent '
            +'session id and depth. You may use `send_message` only for depth-1 entries; deeper entries are '
            +'candidates for `interrupt_agent` only.'
        ),#描述结束
        'parameters':{#参数模式
            'scope':{#作用域
                'type':'string',#字符串
                'enum':['children','descendants'],#两个作用域
                'description':'children (default) lists direct children only; descendants walks the complete tree below you.',#参数说明
            },#scope 结束
        },#parameters 结束
        'output':{#成功返回
            'schema':{#返回模式
                'type':'array',#数组
                'items':{#元素
                    'oneOf':[#子体或诊断
                        {#子体对象
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#字段
                                'kind':{'type':'string','required':True,'enum':['child']},#子体判别
                                'id':{'type':'string','required':True},#会话id
                                'label':{'type':'string','required':True},#标签
                                'status':{'type':'string','required':True,'enum':['running','inactive']},#活状态
                                'parent':{'type':'string'},#可选父id
                                'depth':{'type':'number'},#可选深度
                            },#properties 结束
                        },#子体对象结束
                        {#诊断对象
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#字段
                                'kind':{'type':'string','required':True,'enum':['diagnostic']},#诊断判别
                                'id':{'type':'string','required':True},#会话id
                                'reason':{'type':'string','required':True,'enum':['corrupt','unsupported','unavailable']},#原因
                                'parent':{'type':'string'},#可选父id
                                'depth':{'type':'number'},#可选深度
                            },#properties 结束
                        },#诊断对象结束
                    ],#oneOf 结束
                },#items 结束
            },#schema 结束
            'render':渲染列表,#渲染列表
        },#output 结束
        'execute':执行列举,#执行列举
    }))#defineTool 与 register 结束

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
