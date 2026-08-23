"""Cordis 工具包登记的第一方宿主巡检提供方。

对齐上游 `拓展/tool-cordis/src/providers.ts`。公开面仅中文名。
"""
from ..cordis_服务端 import 宿主内置巡检#宿主内置巡检数据
from .接口目录 import 事件目录,查询服务目录,查询事件目录#目录与查询

__all__=['宿主巡检提供方们','宿主巡检提供方','hostInspectProviders']#仅中文公开名

空输入={'type':'object','properties':{},'additionalProperties':False}#空对象输入模式
任意输出={'description':'JSON data owned by this inspect provider.'}#任意 JSON 输出说明

def 精确输入(字段,说明):#构造可选精确名字段
    """对象上一个可选字符串字段。"""
    return {'type':'object','properties':{字段:{'type':'string','description':说明}},'additionalProperties':False}#模式

服务输入=精确输入('service','Exact Service key. Omit it for the compact Service and method-signature directory.')#服务
事件输入=精确输入('event','Exact Event name. Omit it for the compact Event and listener-signature directory.')#事件
服务输出={'description':'Compact Service directory, or one exact Service contract with only its referenced type declarations.'}#服务输出
事件输出={'description':'Compact Event directory, or one exact Event contract with only its referenced type declarations.'}#事件输出
宿主事件=None#惰性：过滤 cordis/ 前缀后的事件目录

def 取宿主事件():#宿主可见事件
    """去掉 cordis/ 前缀的事件目录。"""
    global 宿主事件#模块缓存
    if 宿主事件 is None:#尚未计算
        宿主事件=[事件 for 事件 in 事件目录 if not str(事件.get('name','')).startswith('cordis/')]#过滤
    return 宿主事件#列表

def 读精确(输入,字段):#读取精确名字段
    """仅接受字符串。"""
    if 输入 is None or isinstance(输入,list) or not isinstance(输入,dict):#非普通对象
        return None#无键
    值=输入.get(字段)#取出
    return 值 if isinstance(值,str) else None#仅字符串

def 登记(标识,说明,方法,查询,输入模式=None,输出模式=None):#组装静态目录提供方
    """返回登记项。"""
    if 输入模式 is None:#缺省
        输入模式=空输入#空
    if 输出模式 is None:#缺省
        输出模式=任意输出#任意
    def 执行(请求方法,输入,_上下文=None):#执行查询
        """未知方法则抛。"""
        if 请求方法!=方法:#未知
            raise Exception('unknown '+标识+' inspect method "'+请求方法+'"')#未知
        return 查询(输入)#委托
    return {#组装登记
        'manifest':{#清单
            'id':标识,#提供方 id
            'description':说明,#说明
            'methods':[{#唯一方法
                'name':方法,#方法名
                'description':说明,#方法说明
                'inputSchema':输入模式,#输入模式
                'outputSchema':输出模式,#输出模式
            }],#方法
        },#清单
        'query':执行,#查询
    }#登记

def 宿主巡检提供方们(上下文):#构造宿主巡检提供方
    """基于生成目录、求值器声明与现场工具作用域构造宿主提供方。"""
    def 查服务(输入):#服务查询
        return 查询服务目录(读精确(输入,'service'))#按键
    def 查事件(输入):#事件查询
        return 查询事件目录(读精确(输入,'event'),取宿主事件())#按名
    def 查内置(_输入):#内置符号
        return {'builtins':宿主内置巡检,'referencedTypes':[]}#清单
    def 工具查询(方法,_输入,查询上下文):#现场工具
        """返回当前 Agent 可调用工具模式。"""
        if 方法!='listTools':#未知
            raise Exception('unknown Tool inspect method "'+方法+'"')#未知
        智能体=查询上下文['agent']#所属 Agent
        return {'tools':上下文.tools.schemas(智能体)}#该 Agent 的工具模式
    return [#登记列表
        登记('Service','Progressive Host Service discovery: compact capability/signature directory, then one exact coding contract.','listService',查服务,服务输入,服务输出),#服务
        登记('Event','Progressive Host Event discovery: compact listener directory, then one exact event contract.','listEvents',查事件,事件输入,事件输出),#事件
        登记('Builtin','Plain-JavaScript symbols available to a dynamic Host half.','listBuiltins',查内置),#内置——文案保持上游；本树 Host 半为 Python
        {#现场工具
            'manifest':{#清单
                'id':'Tool',#提供方 id
                'description':'Tools visible to the requesting Agent, including scoped and dynamic registrations.',#说明
                'methods':[{#查询方法
                    'name':'listTools',#方法名
                    'description':'Return every Tool schema currently callable by this Agent.',#说明
                    'inputSchema':空输入,#无输入
                    'outputSchema':任意输出,#任意 JSON
                }],#方法
            },#清单
            'query':工具查询,#查询
        },#工具
    ]#列表

宿主巡检提供方=宿主巡检提供方们#别名
hostInspectProviders=宿主巡检提供方们#上游名
