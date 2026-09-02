"""面向模型的 `lsp` 工具，叠在 `ctx.lsp` 之上。

对齐上游 `@deepseek-ai/dsh-tool-lsp`。公开面仅中文名。
"""
import json#结果 JSON 文本
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 自然数字段#配置字段
from ...内核.工具 import 定义工具#工具定义
from ..语言服务器 import 语言服务器错误#LSP 错误
from .呈现 import (#呈现与解析
    默认最大位置数,默认最大结果字符数,语言服务器操作列表,
    解析语言服务器参数,格式化位置列表,格式化悬停,呈现语言服务器调用,会话工作目录,
)#呈现面

名称='tool-lsp'#Cordis 插件名
注入=['tools','lsp','systemPrompt']#依赖工具、LSP 与系统提示
name=名称#Cordis 插件名
inject=注入#Cordis 依赖
默认语言服务器工具超时毫秒=60000#默认工具超时

语言服务器提示文本=('Use search/read for ordinary navigation. Use lsp when textual matches are ambiguous or before a change requires precise definitions, implementations, or references. '#提示前段
    +'Positions are one-based line and character (UTF-16) at the cursor; an off-symbol position may return no results. findReferences always includes the declaration.')#提示后段

配置模式={#插件配置
    'maxLocations':自然数字段(最小=1,默认值=默认最大位置数),#位置上限
    'maxResultChars':自然数字段(最小=1,默认值=默认最大结果字符数),#结果字符上限
    'timeoutMs':自然数字段(最小=1,默认值=默认语言服务器工具超时毫秒),#超时预算
}#配置结束

__all__=[#仅中文公开名
    '名称','注入','配置模式','默认语言服务器工具超时毫秒','语言服务器提示文本',
    '应用','默认',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
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
        return 值.等待()#等待
    return 值#同步值

def 断言正整数(名称,值):#配置正整数校验
    """加载期大声失败。"""
    if not isinstance(值,int) or 值<1:#非法
        raise Exception('tool-lsp: '+名称+' must be a positive integer')#拒绝

def 应用(上下文,配置=None):#注册 lsp 工具与系统提示段
    """向工具注册表登记 `lsp`。"""
    配置=配置 or {}#默认空
    已解析={#解析后配置
        'maxLocations':取字段(配置,'maxLocations',默认最大位置数),#位置上限
        'maxResultChars':取字段(配置,'maxResultChars',默认最大结果字符数),#字符上限
        'timeoutMs':取字段(配置,'timeoutMs',默认语言服务器工具超时毫秒),#超时
    }#配置结束
    断言正整数('maxLocations',已解析['maxLocations'])#校验
    断言正整数('maxResultChars',已解析['maxResultChars'])#校验
    断言正整数('timeoutMs',已解析['timeoutMs'])#校验
    上下文.systemPrompt.section({#挂系统提示段
        'name':'tool:lsp',#段名
        'order':上下文.systemPrompt.getSectionOrder('TOOL_LSP'),#顺序
        'text':语言服务器提示文本,#正文
    })#section 结束
    def 渲染(_参数,值):#把结构化结果收成文本
        """按 kind 选择格式化器。"""
        if 取字段(值,'kind')=='locations':#位置结果
            return [{'type':'text','text':格式化位置列表(取字段(值,'locations'),取字段(值,'resolvedWorkspaceUri'),已解析['maxLocations'],已解析['maxResultChars'])}]#文本块
        return [{'type':'text','text':格式化悬停(取字段(值,'hover'),已解析['maxResultChars'])}]#悬停块
    def 执行(参数,执行上下文):#执行一次 LSP 查询
        """要求会话 cwd，并把一基坐标转成缝的零基坐标。"""
        输入=解析语言服务器参数(参数)#校验参数
        工作区根=会话工作目录(执行上下文)#会话 cwd
        if 工作区根 is None:#无工作区
            raise 语言服务器错误('the lsp tool requires a session workspace cwd','LSP_WORKSPACE_REQUIRED')#拒绝
        结果=解开(上下文.lsp.查询({#转发到缝
            'operation':取字段(输入,'operation'),#操作
            'filePath':取字段(输入,'filePath'),#路径
            'position':取字段(输入,'position'),#零基位置
            'workspaceRoot':工作区根,#工作区根
        },取字段(执行上下文,'signal')))#取消信号
        if 取字段(结果,'kind')=='locations':#位置结果
            return {#位置输出
                'kind':'locations',#种类
                'locations':[{'uri':取字段(位置,'uri'),'range':{'start':dict(取字段(取字段(位置,'range'),'start')),'end':dict(取字段(取字段(位置,'range'),'end'))}} for 位置 in 取字段(结果,'locations')],#位置列表
                'resolvedWorkspaceUri':取字段(结果,'resolvedWorkspaceUri'),#工作区 URI
            }#返回结束
        悬停=取字段(结果,'hover')#悬停
        if 悬停 is None:#无悬停
            return {'kind':'hover','hover':None}#空悬停
        输出={'kind':'hover','hover':{'contents':取字段(悬停,'contents')}}#正文
        范围=取字段(悬停,'range')#可选范围
        if 范围 is not None:#有范围
            输出['hover']['range']={'start':dict(取字段(范围,'start')),'end':dict(取字段(范围,'end'))}#带上范围
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
        'output':{'schema':{'type':'object'},'render':渲染},#输出
        'timeoutMs':已解析['timeoutMs'],#超时
        'execute':执行,#执行体
        'presentCall':呈现语言服务器调用,#UI 呈现
    })#defineTool 结束
    上下文.tools.登记(工具)#登记

apply=应用#Cordis 插件入口
默认=应用#默认导出
default=应用#Cordis 默认导出
Config=配置模式#Cordis 配置
