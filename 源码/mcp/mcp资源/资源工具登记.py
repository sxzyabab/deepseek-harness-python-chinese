from ...内核.工具 import 定义工具#定义面向模型的工具
from .渲染 import 渲染资源结果#文本投影

__all__=['登记资源工具']

列表参数={#list 参数
    'server':{'type':'string','required':True,'description':'Configured MCP server name.'},#服务器名
    'cursor':{'type':'string','description':'Continuation cursor returned by this server.'},#游标
}#参数结束

def 输出声明():#规范输出
    """声明 json schema 并以归属文本渲染。"""
    def 渲染(参数,值):#渲染结果
        """把规范结果投成文本块。"""
        return 渲染资源结果(参数['server'],值)#归属渲染
    return {'schema':{'type':'json'},'render':渲染}#output

def 登记资源工具(上下文,请求):#登记三个共享工具
    """在消费方工具作用域登记资源操作。"""
    输出=输出声明()#共用输出
    def 执行体():#生成器副作用
        """登记三个工具。"""
        def 执行列表(参数,执行):#list_mcp_resources
            """列出资源。"""
            请求体={'method':'resources/list'}#方法
            if 'cursor' in 参数 and 参数['cursor'] is not None:#有游标
                请求体['cursor']=参数['cursor']#写入
            return 请求(参数['server'],请求体,执行)#派发
        yield 上下文.tools.register(定义工具({#登记 list
            'name':'list_mcp_resources',#工具名
            'description':'List resources available from an MCP server.',#说明
            'parameters':列表参数,#参数
            'output':输出,#输出
            'execute':执行列表,#执行
        }))#list
        def 执行模板(参数,执行):#list_mcp_resource_templates
            """列出 URI 模板。"""
            请求体={'method':'resources/templates/list'}#方法
            if 'cursor' in 参数 and 参数['cursor'] is not None:#有游标
                请求体['cursor']=参数['cursor']#写入
            return 请求(参数['server'],请求体,执行)#派发
        yield 上下文.tools.register(定义工具({#登记 templates
            'name':'list_mcp_resource_templates',#工具名
            'description':'List parameterized resource URI templates from an MCP server.',#说明
            'parameters':列表参数,#参数
            'output':输出,#输出
            'execute':执行模板,#执行
        }))#templates
        def 执行读取(参数,执行):#read_mcp_resource
            """按 URI 读取资源。"""
            return 请求(参数['server'],{'method':'resources/read','uri':参数['uri']},执行)#派发
        yield 上下文.tools.register(定义工具({#登记 read
            'name':'read_mcp_resource',#工具名
            'description':'Read an MCP resource by URI from the named server. Use a listed URI or an expanded resource template.',#说明
            'parameters':{#参数
                'server':列表参数['server'],#服务器名
                'uri':{'type':'string','required':True,'description':'Resource URI to read.'},#URI
            },#parameters
            'output':输出,#输出
            'execute':执行读取,#执行
        }))#read
    return 上下文.副作用(执行体,'mcpResources.resourceTools')#副作用标签
