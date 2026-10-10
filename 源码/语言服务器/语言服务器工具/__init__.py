'面向模型的 `lsp` 工具，叠在 `ctx.lsp` 之上'
from ...依赖.schemastery import 自然数字段
from ...内核.工具 import 定义工具#工具定义
from ...模型后端.llm import 断言永不#封闭联合穷尽
from ...工具.超时 import 定时器延迟上限毫秒#定时器上限
from ..语言服务器.异常 import 语言服务器错误#LSP 错误
from .呈现 import (#呈现与解析
    默认最大位置数,默认最大结果字符数,语言服务器操作列表,
    解析语言服务器参数,格式化位置列表,格式化悬停,呈现语言服务器调用,渲染uri,
)#呈现面

包名='@deepseek-ai/dsh-tool-lsp'
名称='tool-lsp'
依赖=['tools','lsp','systemPrompt','workingDirectory']
默认语言服务器工具超时毫秒=60000#默认工具超时
语言服务器提示文本=('Use search/read for ordinary navigation. Use lsp when textual matches are ambiguous or before a change requires precise definitions, implementations, or references. '#提示前段
    +'Positions are one-based line and character (UTF-16) at the cursor; an off-symbol position may return no results. findReferences always includes the declaration.')#提示后段
配置={#插件配置
    'maxLocations':自然数字段(最小=1,默认值=默认最大位置数),#位置上限
    'maxResultChars':自然数字段(最小=1,默认值=默认最大结果字符数),#结果字符上限
    'timeoutMs':自然数字段(最小=1,最大=定时器延迟上限毫秒,默认值=默认语言服务器工具超时毫秒),#超时预算
}

位置输出模式={#零基位置
    'type':'object',
    'additionalProperties':False,
    'properties':{
        'line':{'type':'integer','required':True},
        'character':{'type':'integer','required':True},
    },
}#位置结束
范围输出模式={#零基范围
    'type':'object',
    'additionalProperties':False,
    'properties':{
        'start':{**位置输出模式,'required':True},
        'end':{**位置输出模式,'required':True},
    },
}#范围结束
语言服务器输出模式={#位置或悬停
    'oneOf':[
        {
            'type':'object',
            'additionalProperties':False,
            'properties':{
                'kind':{'type':'string','required':True,'const':'locations'},
                'locations':{
                    'type':'array',
                    'required':True,
                    'items':{
                        'type':'object',
                        'additionalProperties':False,
                        'properties':{
                            'uri':{'type':'string','required':True},
                            'range':{**范围输出模式,'required':True},
                        },
                    },
                },
                'resolvedWorkspaceUri':{'type':'string','required':True},
            },
        },
        {
            'type':'object',
            'additionalProperties':False,
            'properties':{
                'kind':{'type':'string','required':True,'const':'hover'},
                'hover':{
                    'required':True,
                    'oneOf':[
                        {'type':'null'},
                        {
                            'type':'object',
                            'additionalProperties':False,
                            'properties':{
                                'contents':{'type':'string','required':True},
                                'range':范围输出模式,
                            },
                        },
                    ],
                },
            },
        },
    ],
}#输出结束

__all__=[
    '包名','名称','依赖','应用','默认','配置','默认语言服务器工具超时毫秒','语言服务器提示文本',
]

def 断言正整数(名称,值):
    '配置入口正整数校验，排除布尔。加载期大声失败'
    if isinstance(值,bool) or isinstance(值,int) is False or 值<1:#非法
        raise Exception('tool-lsp: '+名称+' must be a positive integer')#拒绝

def 断言定时器(名称,值):
    '拒绝会被定时器钳位的超时'
    if isinstance(值,bool) or isinstance(值,int) is False or 值<1 or 值>定时器延迟上限毫秒:#非法
        raise Exception('tool-lsp: '+名称+' must be a positive integer no greater than '+str(定时器延迟上限毫秒))#拒绝

def 应用(上下文,配置值=None):
    '向工具注册表登记 `lsp`'
    if 配置值 is None:#默认空
        配置值={}#空配置
    已解析={#解析后配置
        'maxLocations':配置值['maxLocations'] if 'maxLocations' in 配置值 else 默认最大位置数,#位置上限
        'maxResultChars':配置值['maxResultChars'] if 'maxResultChars' in 配置值 else 默认最大结果字符数,#字符上限
        'timeoutMs':配置值['timeoutMs'] if 'timeoutMs' in 配置值 else 默认语言服务器工具超时毫秒,#超时
    }
    断言正整数('maxLocations',已解析['maxLocations'])#校验
    断言正整数('maxResultChars',已解析['maxResultChars'])#校验
    断言定时器('timeoutMs',已解析['timeoutMs'])#校验
    上下文.systemPrompt.段落({#挂系统提示段
        'name':'tool:lsp',#段名
        'order':上下文.systemPrompt.获取段落顺序('TOOL_LSP'),#中央段落顺序
        'text':语言服务器提示文本,#正文
    })#段落结束
    def 渲染(_参数,值):
        '按 kind 选择格式化器。值是工具结果 dict'
        if 值['kind']=='locations':#位置结果
            return [{'type':'text','text':格式化位置列表(值['locations'],值['resolvedWorkspaceUri'],已解析['maxLocations'],已解析['maxResultChars'])}]#文本块
        if 值['kind']=='hover':#悬停结果
            return [{'type':'text','text':格式化悬停(值['hover'],已解析['maxResultChars'])}]#悬停块
        return 断言永不(值,'tool-lsp output')#封闭联合
    def 拷贝位置(位置):
        '只保留线协议上的行与列'
        return {'line':位置['line'],'character':位置['character']}#位置
    def 执行(参数,执行上下文):
        '要求会话工作区，并把一基坐标转成缝的零基坐标。参数与执行上下文是 dict'
        输入=解析语言服务器参数(参数)#校验参数
        智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#调用智能体
        if 智能体 is None:#无智能体
            工作区根=None#无工作区
        else:#有智能体
            工作区根=上下文.workingDirectory.ensure(智能体,执行上下文['signal'] if 'signal' in 执行上下文 else None)#确保目录还在
        if 工作区根 is None:#无工作区
            raise 语言服务器错误('the lsp tool requires a session workspace cwd','LSP_WORKSPACE_REQUIRED')#拒绝
        结果=上下文.lsp.查询({#转发到缝
            'operation':输入['operation'],#操作
            'filePath':输入['filePath'],#路径
            'position':输入['position'],#零基位置
            'workspaceRoot':工作区根,#工作区根
        },执行上下文['signal'] if 'signal' in 执行上下文 else None)#取消信号
        if 结果['kind']=='locations':#位置结果
            位置列表=[]#拷贝位置
            for 位置 in 结果['locations']:#逐条
                范围=位置['range']#范围
                位置列表.append({'uri':位置['uri'],'range':{'start':拷贝位置(范围['start']),'end':拷贝位置(范围['end'])}})#位置
            return {#位置输出
                'kind':'locations',#种类
                'locations':位置列表,#位置列表
                'resolvedWorkspaceUri':结果['resolvedWorkspaceUri'],#工作区 URI
            }#返回结束
        if 结果['kind']!='hover':#封闭联合
            return 断言永不(结果,'tool-lsp result')#穷尽
        悬停=结果['hover'] if 'hover' in 结果 else None#悬停
        if 悬停 is None:#无悬停
            return {'kind':'hover','hover':None}#空悬停
        输出={'kind':'hover','hover':{'contents':悬停['contents']}}#正文
        if 'range' in 悬停 and 悬停['range'] is not None:#有范围
            范围=悬停['range']#范围
            输出['hover']['range']={'start':拷贝位置(范围['start']),'end':拷贝位置(范围['end'])}#带上范围
        return 输出#悬停输出
    工具=定义工具({#定义 lsp 工具
        'name':'lsp',#工具名
        'description':'Query a language server for precise code navigation. operation is one of goToDefinition, findReferences, goToImplementation, hover. line and character are one-based UTF-16 cursor coordinates. findReferences includes the declaration.',#描述
        'parameters':{#参数模式
            'operation':{'type':'string','required':True,'enum':语言服务器操作列表,'description':'goToDefinition, findReferences, goToImplementation, or hover.'},#操作
            'file_path':{'type':'string','required':True,'description':'The source file to query, relative to the workspace or absolute.'},#路径
            'line':{'type':'number','required':True,'description':'One-based line of the cursor.'},#行
            'character':{'type':'number','required':True,'description':'One-based UTF-16 column of the cursor.'},#列
        },#parameters 结束
        'output':{'schema':语言服务器输出模式,'render':渲染},#输出
        'timeoutMs':已解析['timeoutMs'],#超时
        'execute':执行,#执行体
        'presentCall':呈现语言服务器调用,#UI 呈现
    })#defineTool 结束
    上下文.tools.登记(工具)#登记

默认=应用
name=名称#框架槽
inject=依赖#框架槽
Config=配置#框架槽
apply=应用#框架槽
default=默认#框架槽
