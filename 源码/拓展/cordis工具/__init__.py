import json
from ...内核.工具 import 定义工具
from .呈现 import 呈现列表调用,呈现查询调用,巡检错误

__all__=['包名','名称','依赖','应用','默认','巡检错误']

包名='@deepseek-ai/dsh-tool-cordis'
名称='tool-cordis'
依赖=['tools','cordisInspect']

def 需要智能体(执行):
    """工具执行必须带智能体。"""
    if 'agent' not in 执行 or 执行['agent'] is None:
        raise 巡检错误('Cordis 巡检需要由智能体支撑的会话')
    return 执行['agent']

def 渲染(参数,值):
    """缩进 JSON。"""
    return [{'type':'text','text':json.dumps(值,ensure_ascii=False,indent=2,separators=(',',':'),allow_nan=False)}]

def 应用(上下文):
    """登记只读运行时巡检工具；Host 提供方由宿主插件按进程登记。"""
    def 执行列表(参数,执行上下文):
        """列出当前已知的全部巡检提供方。"""
        return {'providers':上下文.cordisInspect.列出()}
    上下文.tools.登记(定义工具({
        'name':'cordis_inspect_list',
        'description':'列出宿主当前已知的全部 Cordis 巡检提供方，包括本地宿主提供方以及从客户端同步来的最新清单。每条含平台、用途、只读方法与输入/输出模式。编写或配置插件前先调用本工具，再从其结果中选出提供方与方法交给 cordis_inspect_query。不要猜测名字，也不要把巡检方法当成插件代码可调用的业务服务。',
        'parameters':{},
        'output':{
            'schema':{'type':'json'},
            'render':渲染,
        },
        'execute':执行列表,
        'presentCall':呈现列表调用,
    }))
    def 执行查询(参数,执行上下文):
        """跑提供方声明的只读查询。"""
        数据=上下文.cordisInspect.查询(
            参数['platform'],
            参数['provider'],
            参数['method'],
            参数['input'] if 'input' in 参数 else None,
            需要智能体(执行上下文),
            执行上下文['signal'] if 'signal' in 执行上下文 else None,
        )
        return {'platform':参数['platform'],'provider':参数['provider'],'method':参数['method'],'data':数据}
    上下文.tools.登记(定义工具({
        'name':'cordis_inspect_query',
        'description':'运行巡检提供方声明的只读查询。platform、provider 与 method 必须来自 cordis_inspect_list，input 必须满足该方法的模式。编写插件代码前用本工具读取精确服务方法、事件模式、插件 Config 模式、工具模式、主题令牌或现场槽树与 props。宿主查询在本地执行。客户端查询等待第一份有效页面响应，直到有页面回答或工具被取消。本工具不能调用业务服务方法，也不能修改运行时。',
        'parameters':{
            'platform':{'type':'string','required':True,'enum':['host','client'],'description':'拥有该提供方的运行时平台。'},
            'provider':{'type':'string','required':True,'description':'cordis_inspect_list 返回的精确提供方 ID。'},
            'method':{'type':'string','required':True,'description':'提供方清单声明的精确方法名。'},
            'input':{'type':'json','description':'可选查询输入；必须满足该方法的输入模式。'},
        },
        'output':{
            'schema':{'type':'json'},
            'render':渲染,
        },
        'execute':执行查询,
        'presentCall':呈现查询调用,
    }))

name=名称
inject=依赖
apply=应用
default=应用
默认=应用
