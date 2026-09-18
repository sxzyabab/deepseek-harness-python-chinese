import json#JSON 序列化
from ...内核.工具 import 定义工具#工具定义工厂
from .提示 import cordis系统提示#系统提示词
from .呈现 import 呈现巡检列表调用,呈现巡检查询调用#展示函数
from .提供方 import 列出宿主巡检提供方#宿主巡检提供方

__all__=['名称','注入','应用','工具错误']#仅中文公开名

名称='tool-cordis'#插件名
注入=['tools','systemPrompt','cordisInspect']#硬依赖服务

class 工具错误(Exception):
    """Cordis 巡检工具失败。"""
    pass#消息在构造时传入

def 要求智能体(执行):
    """工具执行必须带 Agent。执行为 dict。"""
    智能体=执行['agent'] if 'agent' in 执行 else None#调用方 Agent
    if 智能体 is None:#无会话
        raise 工具错误('Cordis inspection requires an Agent-backed session')#失败
    return 智能体#返回

def 列表渲染(参数,值):
    """缩进 JSON 文本。"""
    return [{'type':'text','text':json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)}]#文本块

def 应用(上下文):
    """登记只读运行时巡检工具。"""
    上下文.systemPrompt.段落({'name':'tool:cordis','order':115,'text':cordis系统提示})#挂上系统提示词段

    def 登记一项(项):
        """闭包：按 Fiber 登记一个巡检提供方。"""
        def 登记():
            """副作用体。"""
            上下文.cordisInspect.登记(项)#登记
        return 登记#副作用

    for 提供方 in 列出宿主巡检提供方(上下文):#每个宿主巡检提供方
        上下文.副作用(登记一项(提供方),'tool-cordis: inspect '+提供方['manifest']['id'])#按 Fiber 登记

    def 列表执行(参数,执行):
        """列出全部巡检提供方。"""
        return {'providers':上下文.cordisInspect.列出()}#列出全部提供方

    上下文.tools.登记(定义工具({#登记巡检列表工具
        'name':'cordis_inspect_list',#工具名
        'description':(#工具说明
            'List every Cordis Inspect Provider currently known to the Host, including local Host Providers and the latest '
            +'manifests synchronized from the Client. Each entry includes its platform, purpose, read-only methods, and '
            +'input/output schemas. Call this Tool before writing or configuring a plugin, then select the provider and '
            +'method for cordis_inspect_query from its result. Do not guess names or treat an Inspect method as a business '
            +'Service that Plugin code can call.'
        ),#说明
        'parameters':{},#无参数
        'output':{'schema':{'type':'json'},'render':列表渲染},#输出
        'execute':列表执行,#列出全部提供方
        'presentCall':呈现巡检列表调用,#调用展示
    }))#列表工具结束

    def 查询执行(参数,执行):
        """委托巡检服务。参数与执行为 dict。"""
        输入=参数['input'] if 'input' in 参数 else None#可选输入
        信号=执行['signal'] if 'signal' in 执行 else None#可选中止
        数据=上下文.cordisInspect.查询(参数['platform'],参数['provider'],参数['method'],输入,要求智能体(执行),信号)#查询
        return {'platform':参数['platform'],'provider':参数['provider'],'method':参数['method'],'data':数据}#回显

    上下文.tools.登记(定义工具({#登记巡检查询工具
        'name':'cordis_inspect_query',#工具名
        'description':(#工具说明
            'Run a read-only query explicitly declared by an Inspect Provider. platform, provider, and method must come '
            +'from cordis_inspect_list, and input must satisfy that method\'s schema. Use this Tool before writing plugin code '
            +'to read exact Service methods, Event modes, Builtin signatures, Tool schemas, theme tokens, or live Slot '
            +'trees and props. Host queries run locally. A Client query waits for the first valid page response and '
            +'remains pending until a page answers or the Tool is cancelled. This Tool cannot invoke business Service '
            +'methods or modify the runtime. For Service.listService and Event.listEvents, query without input to navigate '
            +'the compact signature directory, then query the exact service or event for its structured contract and '
            +'referenced types. For Slots.listSubTree, query without root to navigate the compact tree, then query an '
            +'exact Slot root for its complete registration contract and props; an exact Factory root returns its identity, '
            +'scope, and registrant.'
        ),#说明
        'parameters':{#参数
            'platform':{'type':'string','required':True,'enum':['host','client'],'description':'Runtime platform that owns the Provider.'},#平台
            'provider':{'type':'string','required':True,'description':'Exact Provider ID returned by cordis_inspect_list.'},#提供方
            'method':{'type':'string','required':True,'description':'Exact method name declared by the Provider manifest.'},#方法
            'input':{'type':'json','description':'Optional query input; it must satisfy the method input schema.'},#可选输入
        },#参数
        'output':{'schema':{'type':'json'},'render':列表渲染},#输出
        'execute':查询执行,#执行
        'presentCall':呈现巡检查询调用,#展示
    }))#查询工具结束

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
