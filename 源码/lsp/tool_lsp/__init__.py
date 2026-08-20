"""架在 `ctx.lsp` 上、面向模型的 `lsp` 工具。一个只读工具，四种操作（`goToDefinition`/`findReferences`/`goToImplementation`/`hover`）；把一基 UTF-16 光标坐标换成 seam 的零基位置，强制要求会话工作区且无回退，封顶并渲染结果，并挂上可配置超时预算供 `dsh-tool-call-timeout-policy` 强制。运行时只注入 `tools`、`lsp` 和 `systemPrompt`，不导入任何提供方。

命名空间插件（具名导出，无默认导出）。
"""
from schemastery import 模式#导入配置校验
from tools import 定义工具#导入工具定义
from llm import 断言永不#导入封闭联合穷尽断言
from lsp import 语言服务器错误#导入LSP结构化错误
from timeout import 定时器延迟上限毫秒#导入定时器上限
from cordis.工具 import 是否thenable#可等待判定
from .渲染 import (#导入渲染、校验与默认上限
    默认最大位置数,#位置条数默认上限
    默认最大结果字符,#完整结果默认字符上限
    格式化悬停,#悬停渲染
    格式化位置,#位置渲染
    语言服务器操作,#四种操作元组
    解析语言服务器参数,#参数校验与换算
    呈现语言服务器调用,#UI 展示
    渲染网址,#URI 显示路径
)#渲染面导入结束
from .会话工作区 import 会话工作区#导入会话工作区推导

名称='tool-lsp'#供加载器诊断用的 Cordis 插件名
注入=['tools','lsp','systemPrompt']#依赖工具、lsp 与系统提示词
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
默认语言服务器工具超时毫秒=60000#默认工具调用超时预算（毫秒），覆盖排队的打开/查询/关闭生命周期
语言服务器提示文本=(#把 LSP 定位为精确辅助的稳定系统提示词指引（字面量不翻译）
    'Use search/read for ordinary navigation. Use lsp when textual matches are ambiguous or before a change requires precise definitions, implementations, or references. Positions are one-based line and character (UTF-16) at the cursor; an off-symbol position may return no results. findReferences always includes the declaration.'#面向模型的 LSP 使用指引正文
)#语言服务器提示文本结束
配置=模式.对象({#插件配置：结果上限与超时预算
    'maxLocations':模式.数字().默认(默认最大位置数),#追加省略标记前可渲染的最大位置数（默认 100）
    'maxResultChars':模式.数字().默认(默认最大结果字符),#完整渲染结果的最大字符数，含截断元数据（默认 16000）
    'timeoutMs':模式.数字().最大(定时器延迟上限毫秒).默认(默认语言服务器工具超时毫秒),#工具调用超时预算，毫秒（默认 60000）
})#Config schema 结束
Config=配置#Cordis配置模式
位置输出模式={#位置输出 schema
    'type':'object',#对象
    'additionalProperties':False,#不许多余键
    'properties':{#行与列
        'line':{'type':'integer','required':True},#零基行
        'character':{'type':'integer','required':True},#零基列
    },#properties 结束
}#位置输出 schema 结束
范围输出模式={#范围输出 schema
    'type':'object',#对象
    'additionalProperties':False,#不许多余键
    'properties':{#起止
        'start':{**位置输出模式,'required':True},#起点必填
        'end':{**位置输出模式,'required':True},#终点必填
    },#properties 结束
}#范围输出 schema 结束

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

def 是否整数(值):#对齐 JS Number.isInteger
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 断言正整数(名称,值):#校验正整数配置
    """加载时拒绝非正整数配置值，让错误配置大声失败。"""
    if not 是否整数(值) or 值<1:#非正整数
        raise Exception('tool-lsp: '+名称+' must be a positive integer')#加载时失败

def 断言定时器(名称,值):#校验定时器预算
    """拒绝会被 Node 钳位、而不是按配置调度的定时器值。"""
    if not 是否整数(值) or 值<1 or 值>定时器延迟上限毫秒:#超出可调度范围
        raise Exception('tool-lsp: '+名称+' must be a positive integer no greater than '+str(定时器延迟上限毫秒))#加载时失败

def 应用(上下文,配置值):#注册工具与提示词
    """注册 `lsp` 工具及其系统提示词指引。
    @param 上下文 - 插件上下文（必须注入 tools、lsp、systemPrompt）
    @param 配置值 - 已解析的插件配置
    """
    最大位置数=取字段(配置值,'maxLocations',默认最大位置数)#位置上限
    最大结果字符=取字段(配置值,'maxResultChars',默认最大结果字符)#字符上限
    超时毫秒=取字段(配置值,'timeoutMs',默认语言服务器工具超时毫秒)#超时预算
    断言正整数('maxLocations',最大位置数)#校验位置上限
    断言正整数('maxResultChars',最大结果字符)#校验字符上限
    断言定时器('timeoutMs',超时毫秒)#校验超时预算
    上下文.systemPrompt.section({#挂系统提示词段
        'name':'tool:lsp',#段落名
        'order':112,#顺序
        'text':语言服务器提示文本,#指引正文
    })#系统提示词段结束
    def 渲染(_参数,值):#按结果 kind 渲染给模型
        """按封闭联合 kind 分派原生文本渲染。"""
        种类=取字段(值,'kind')#结果种类
        if 种类=='locations':#导航结果
            return [{'type':'text','text':格式化位置(#按上限格式化位置
                取字段(值,'locations'),#位置列表
                取字段(值,'resolvedWorkspaceUri'),#规范工作区 URI
                最大位置数,#条数上限
                最大结果字符,#字符上限
            )}]#文本块
        if 种类=='hover':#悬停结果
            return [{'type':'text','text':格式化悬停(取字段(值,'hover'),最大结果字符)}]#按上限格式化悬停
        return 断言永不(值,'tool-lsp output')#穷尽断言
    def 执行(参数,执行上下文):#执行一次 lsp 查询
        """校验参数、取会话工作区、经 seam 查询并映射成工具输出。"""
        输入=解析语言服务器参数(参数)#校验并换算坐标
        工作区根=会话工作区(执行上下文)#取会话工作区
        if 工作区根 is None:#没有会话 cwd
            raise 语言服务器错误('the lsp tool requires a session workspace cwd','LSP_WORKSPACE_REQUIRED')#无回退，大声失败
        结果=解开(上下文.lsp.query({#把取消信号转给 seam
            'operation':取字段(输入,'operation'),#语义操作
            'filePath':取字段(输入,'filePath'),#源路径
            'position':取字段(输入,'position'),#零基光标
            'workspaceRoot':工作区根,#会话工作区根
        },取字段(执行上下文,'signal')))#查询并解开承诺
        种类=取字段(结果,'kind')#结果种类
        if 种类=='locations':#导航
            位置输出=[]#工具输出位置列表
            for 位置 in 取字段(结果,'locations'):#逐条拷贝范围
                范围=取字段(位置,'range')#范围
                起点=取字段(范围,'start')#起点
                终点=取字段(范围,'end')#终点
                位置输出.append({#位置条目
                    'uri':取字段(位置,'uri'),#文档 URI
                    'range':{#半开范围
                        'start':{'line':取字段(起点,'line'),'character':取字段(起点,'character')},#起点
                        'end':{'line':取字段(终点,'line'),'character':取字段(终点,'character')},#终点
                    },#range 结束
                })#位置条目结束
            return {#locations 输出
                'kind':'locations',#导航 kind
                'locations':位置输出,#位置列表
                'resolvedWorkspaceUri':取字段(结果,'resolvedWorkspaceUri'),#规范工作区 URI
            }#locations 输出结束
        if 种类=='hover':#悬停
            悬停=取字段(结果,'hover')#归一化悬停或 null
            if 悬停 is None:#无悬停
                return {'kind':'hover','hover':None}#空悬停输出
            悬停输出={'contents':取字段(悬停,'contents')}#悬停正文
            范围=取字段(悬停,'range')#可选范围
            if 范围 is not None:#有范围
                起点=取字段(范围,'start')#起点
                终点=取字段(范围,'end')#终点
                悬停输出['range']={#带上范围
                    'start':{'line':取字段(起点,'line'),'character':取字段(起点,'character')},#起点
                    'end':{'line':取字段(终点,'line'),'character':取字段(终点,'character')},#终点
                }#range 结束
            return {'kind':'hover','hover':悬停输出}#hover 输出结束
        return 断言永不(结果,'tool-lsp result')#穷尽断言
    上下文.tools.register(定义工具({#注册 lsp 工具
        'name':'lsp',#工具名
        'description':(#面向模型说明（字面量不翻译）
            'Query a language server for precise code navigation. operation is one of goToDefinition, findReferences, goToImplementation, hover. line and character are one-based UTF-16 cursor coordinates. findReferences includes the declaration.'#工具描述正文
        ),#描述结束
        'parameters':{#参数模式
            'operation':{#操作枚举
                'type':'string',#字符串
                'required':True,#必填
                'enum':list(语言服务器操作),#四种操作
                'description':'goToDefinition, findReferences, goToImplementation, or hover.',#操作说明
            },#operation 结束
            'file_path':{'type':'string','required':True,'description':'The source file to query, relative to the workspace or absolute.'},#源文件
            'line':{'type':'number','required':True,'description':'One-based line of the cursor.'},#一基行
            'character':{'type':'number','required':True,'description':'One-based UTF-16 column of the cursor.'},#一基列
        },#parameters 结束
        'output':{#输出模式与渲染
            'schema':{#封闭联合
                'oneOf':[#locations 或 hover
                    {#导航分支
                        'type':'object',#对象
                        'additionalProperties':False,#不许多余键
                        'properties':{#字段
                            'kind':{'type':'string','required':True,'const':'locations'},#locations kind
                            'locations':{#位置数组
                                'type':'array',#数组
                                'required':True,#必填
                                'items':{#单条位置
                                    'type':'object',#对象
                                    'additionalProperties':False,#不许多余键
                                    'properties':{#uri 与 range
                                        'uri':{'type':'string','required':True},#文档 URI
                                        'range':{**范围输出模式,'required':True},#范围必填
                                    },#properties 结束
                                },#items 结束
                            },#locations 结束
                            'resolvedWorkspaceUri':{'type':'string','required':True},#规范工作区 URI
                        },#properties 结束
                    },#导航分支结束
                    {#悬停分支
                        'type':'object',#对象
                        'additionalProperties':False,#不许多余键
                        'properties':{#字段
                            'kind':{'type':'string','required':True,'const':'hover'},#hover kind
                            'hover':{#悬停或 null
                                'required':True,#必填
                                'oneOf':[#null 或对象
                                    {'type':'null'},#无悬停
                                    {#有悬停
                                        'type':'object',#对象
                                        'additionalProperties':False,#不许多余键
                                        'properties':{#正文与可选范围
                                            'contents':{'type':'string','required':True},#悬停正文
                                            'range':范围输出模式,#可选范围
                                        },#properties 结束
                                    },#有悬停结束
                                ],#oneOf 结束
                            },#hover 结束
                        },#properties 结束
                    },#悬停分支结束
                ],#oneOf 结束
            },#schema 结束
            'render':渲染,#按 kind 渲染
        },#output 结束
        'timeoutMs':超时毫秒,#超时预算
        'execute':执行,#执行入口
        'presentCall':呈现语言服务器调用,#调用中 UI
    }))#注册 lsp 工具结束

apply=应用#Cordis插件入口
