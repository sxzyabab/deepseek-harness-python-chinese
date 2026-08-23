"""全局命名的 `list_agents` 工具：`ctx.subagents.列举子体们()` 可续跑投影上的薄面向模型适配器，`descendants` 作用域则走 `ctx.subagents.列举后代们()`。它与根 `send_message` 插件分开可加载，以便部署能登记续跑投递而不暴露发现。

对齐上游 `tool-subagent-control/src/list-agents.ts`。公开面仅中文名。
"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现
是否thenable=cordis.工具.是否thenable#可等待判定
from ...内核.工具 import 定义工具#导入工具定义
from ...模型后端.llm import 断言永不#导入穷尽检查

名称='tool-subagent-list-agents'#Cordis插件名
注入=['tools','subagents','agents']#依赖工具、子智能体与智能体注册表
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）

列举智能体作用域=Literal['children','descendants']#列举作用域

class 列举智能体请求(TypedDict):#模型请求
    scope:NotRequired[列举智能体作用域]#可选作用域

class 列举智能体规格(TypedDict):#内部必填规格
    scope:列举智能体作用域#已解析作用域

class 列举智能体子体行(TypedDict):#子体行
    kind:Literal['child']#子体
    id:str#会话id
    label:str#标签
    status:Literal['running','idle','ready']#活注册表状态
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
    '名称','注入','应用','默认',
    '列举智能体作用域','列举智能体请求','列举智能体规格',
    '列举智能体子体行','列举智能体诊断行','列举智能体条目',
    '解析列举智能体请求','状态于','投影','取字段','解开',
]

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段；映射优先于属性。"""
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

def 解析列举智能体请求(请求):#解析请求
    """把可选模型请求解析成内部必填作用域规格；缺省 scope 为 `children`。"""
    作用域=取字段(请求,'scope')#读作用域
    if 作用域 is None:#未给出
        作用域='children'#默认直接子
    return {'scope':作用域}#已解析规格

def 状态于(智能体们,标识):#读活状态
    """经活 Agent 注册表细化一个候选的状态：活动驱动为 `running`，回合之间驻留的 Agent（可能在等它启动的智能体）为 `idle`，没有活 Agent 时为 `ready`。`ready` 保留可恢复性，而不把未活动对话呈现为待收集的终态结果。"""
    取=getattr(智能体们,'get',None) or getattr(智能体们,'取',None)#活注册表取法
    智能体=取(标识) if 取 is not None else None#活智能体
    if 智能体 is None:#只在存储里
        return 'ready'#可恢复
    状态=取字段(智能体,'status')#读状态
    if 状态=='running':#活动驱动
        return 'running'#正在工作
    return 'idle'#驻留空闲

def 投影(智能体们,条目,位置=None):#投影一行
    """把一行服务条目投影成面向模型的条目，或省略一次性子体。"""
    if 位置 is None:#无树位置
        处={}#空位置
    else:#有树位置
        处={'parent':取字段(位置,'parentId'),'depth':取字段(位置,'depth')}#位置字段
    if 取字段(条目,'kind')=='diagnostic':#诊断行原样带位置
        行={'kind':'diagnostic','id':取字段(条目,'id'),'reason':取字段(条目,'reason')}#诊断基行
        行.update(处)#并入位置
        return 行#诊断
    # 一次性子体不能被 send_message 续跑，因此模型从不选它们；发现仍为后代遍历了它们。
    if 取字段(条目,'mode')!='continuable':#非可续跑
        return None#省略一次性
    行={#可续跑子体行
        'kind':'child',#子体
        'id':取字段(条目,'id'),#会话id
        'label':取字段(条目,'label'),#标签
        'status':状态于(智能体们,取字段(条目,'id')),#活状态
    }#基行
    行.update(处)#并入可选位置
    return 行#子体行

def 应用(上下文):#登记 list_agents
    """登记 `list_agents` 工具。"""
    def 渲染列表(参数,条目们):#渲染列表
        """按作用域渲染列表文本块；空列表渲染 `(no subagents)`。"""
        请求=解析列举智能体请求(参数)#解析作用域
        if len(条目们)==0:#空列表
            正文='(no subagents)'#空文案（字面量不译）
        else:#有条目
            行们=[]#收集行文案
            for 条目 in 条目们:#逐行
                # 后代行始终携带位置；直接子行从不渲染它。String() 覆盖模式可选形态，没有死回退分支。
                if 取字段(请求,'scope')=='descendants':#后代才带位置
                    处=' parent='+str(取字段(条目,'parent'))+' depth='+str(取字段(条目,'depth'))#位置文案
                else:#直接子
                    处=''#无位置
                if 取字段(条目,'kind')=='child':#子体行
                    行们.append(str(取字段(条目,'id'))+' ['+str(取字段(条目,'status'))+']'+处+' — '+str(取字段(条目,'label')))#子体行
                else:#诊断行
                    行们.append(str(取字段(条目,'id'))+' [diagnostic: '+str(取字段(条目,'reason'))+']'+处)#诊断行
            正文='\n'.join(行们)#换行拼接
        return [{'type':'text','text':正文}]#文本块
    def 执行列举(参数,执行元数据):#执行列举
        """按作用域列举可续跑子体或后代树，并投影为面向模型的条目。"""
        父=取字段(执行元数据,'agent')#调用方智能体
        if not 父:#无智能体调用方
            # 非智能体调用方没有可列举其子的会话。
            raise Exception('list_agents requires a calling agent (exec.agent was undefined)')#拒绝
        请求=解析列举智能体请求(参数)#解析作用域
        作用域=取字段(请求,'scope')#已解析作用域
        信号=取字段(执行元数据,'signal')#取消信号
        # 注册表会排空已启动的工具体，因此扫描必须观察本次调用的信号，而不是取消后仍跑完慢目录。
        if 作用域=='children':#直接子
            条目们=解开(上下文.subagents.列举子体们(取字段(父,'id'),信号))#列举直接子
            结果=[]#投影结果
            for 条目 in 条目们:#逐条投影
                投影行=投影(上下文.agents,条目)#投影
                if 投影行 is not None:#非省略
                    结果.append(投影行)#收下
            return 已兑现(结果)#返回投影
        if 作用域=='descendants':#整棵树
            条目们=解开(上下文.subagents.列举后代们(取字段(父,'id'),信号))#列举后代
            结果=[]#投影结果
            for 条目 in 条目们:#逐条投影
                投影行=投影(上下文.agents,条目,条目)#带位置投影
                if 投影行 is not None:#非省略
                    结果.append(投影行)#收下
            return 已兑现(结果)#返回投影
        # 解析器在分派前已把 schema 校验过的封闭作用域归一化。
        return 断言永不(作用域,'list_agents scope')#不可达
    上下文.tools.register(定义工具({#登记 list_agents
        'name':'list_agents',#工具名（协议字面量不译）
        'description':(#工具描述（字面量不译）
            'List your continuable background subagents by durable id and label. Use it to recall which ones '
            +'you started, not to poll for completion — you are told when one finishes. Status comes from the live '
            +'registry: running means the agent is working right now, idle means it is loaded but between turns '
            +'(it may be waiting on agents it started), and ready means it exists only in storage — resumable, not '
            +'terminal, and not a result waiting to be collected; a `send_message` starts a new turn on the same '
            +'conversation, and a direct child remains a `send_message` candidate in every status. The snapshot is not a delivery '
            +'promise — `send_message` performs the authoritative check and may still fail. Children that could '
            +'not be read are reported as diagnostics instead of being silently dropped. Scope `descendants` '
            +'walks the whole tree below you in stable pre-order, annotating each entry with its durable direct-parent '
            +'session id and depth. You may use `send_message` only for depth-1 entries; deeper entries are '
            +'candidates for `interrupt_agent` only.'
        ),#描述结束
        'parameters':{#参数模式
            'scope':{#作用域
                'type':'string',#字符串
                'enum':['children','descendants'],#两个作用域
                'description':'children (default) lists direct children only; descendants walks the complete tree below you.',#参数说明（字面量不译）
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
                                'status':{'type':'string','required':True,'enum':['running','idle','ready']},#活状态
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

apply=应用#Cordis插件入口（协议槽）
默认=应用#中文默认导出
default=应用#Cordis默认导出（协议槽）
