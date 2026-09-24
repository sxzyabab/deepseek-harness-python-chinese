from ..cordis服务端.巡检注册表 import 宿主巡检提供方登记
from .名录 import 事件目录,查询事件目录,查询服务目录
from .配置 import 查询现场配置
from .呈现 import 巡检错误

__all__=['宿主巡检提供方']

def 精确输入(字段,说明):
    """构造可选精确名字段。"""
    return {'type':'object','properties':{字段:{'type':'string','description':说明}},'additionalProperties':False}

def 读精确(输入,字段):
    """读取精确名字段。"""
    if not isinstance(输入,dict):
        return None
    值=输入[字段] if 字段 in 输入 else None
    return 值 if isinstance(值,str) else None

空输入={'type':'object','properties':{},'additionalProperties':False}
任意输出={'description':'本巡检提供方拥有的 JSON 数据。'}
服务输入=精确输入('service','精确 Service 键。省略则返回压缩的服务与方法签名目录。')
事件输入=精确输入('event','精确 Event 名。省略则返回压缩的事件与监听签名目录。')
服务输出={'description':'压缩服务目录，或一份精确服务契约（只含其引用到的类型声明）。'}
事件输出={'description':'压缩事件目录，或一份精确事件契约（只含其引用到的类型声明）。'}
配置输入={
    'type':'object',
    'properties':{
        'entry':{'type':'string','description':'目录中的精确 Loader 条目 id；返回该条目投影后的 Config 模式。'},
        'name':{'type':'string','description':'精确插件包名；把目录限制到它的条目。'},
        'offset':{'type':'number','description':'从 0 起的目录偏移；默认 0。'},
        'limit':{'type':'number','description':'目录页大小，1 到 100；默认 25。'},
    },
    'additionalProperties':False,
}
配置输出={'description':'一页现场条目（含 patch id、Config 状态、total 与 nextOffset），或一条目投影后的 JSON Schema（含共享定义、省略接受与投影限制）。'}
宿主事件=[事件 for 事件 in 事件目录 if not 事件['name'].startswith('cordis/')]

def 宿主巡检提供方(上下文):
    """基于生成目录、现场 Config 与按智能体可见的工具构造宿主提供方。"""
    def 查服务(输入):
        """按精确键查询服务目录。"""
        return 查询服务目录(读精确(输入,'service'))
    def 查事件(输入):
        """按精确名查询宿主事件目录。"""
        return 查询事件目录(读精确(输入,'event'),宿主事件)
    def 查配置(输入):
        """查询现场插件 Config。"""
        return 查询现场配置(上下文,输入)
    def 查工具(方法,_输入=None,查询上下文=None):
        """返回该智能体当前可调用的工具模式。"""
        if 方法!='listTools':
            raise 巡检错误('未知 Tool 巡检方法 "'+方法+'"')
        智能体=None if 查询上下文 is None else 查询上下文.智能体
        return {'tools':上下文.tools.诸模式(智能体)}
    工具登记=宿主巡检提供方登记({
        'id':'Tool',
        'description':'请求智能体可见的工具，含作用域与动态登记。',
        'methods':[{
            'name':'listTools',
            'description':'返回该智能体当前可调用的全部工具模式。',
            'inputSchema':空输入,
            'outputSchema':任意输出,
        }],
    },查工具)
    return [
        组装登记(
            'Service',
            '渐进宿主服务发现：先压缩能力/签名目录，再查一份精确编码契约。',
            'listService',
            查服务,
            服务输入,
            服务输出,
        ),
        组装登记(
            'Event',
            '渐进宿主事件发现：先压缩监听目录，再查一份精确事件契约。',
            'listEvents',
            查事件,
            事件输入,
            事件输出,
        ),
        组装登记(
            'Config',
            '渐进现场插件 Config 发现：先分页目录（含模式状态），再查一条目的精确 JSON Schema。',
            'listConfigs',
            查配置,
            配置输入,
            配置输出,
        ),
        工具登记,
    ]

def 组装登记(标识,说明,方法,查询实现,输入模式=None,输出模式=None):
    """组装只有一个查询方法的静态目录提供方。"""
    if 输入模式 is None:
        输入模式=空输入
    if 输出模式 is None:
        输出模式=任意输出
    def 查询(请求方法,输入=None,查询上下文=None):
        """委托给目录查询。"""
        if 请求方法!=方法:
            raise 巡检错误('未知 '+标识+' 巡检方法 "'+请求方法+'"')
        return 查询实现(输入)
    return 宿主巡检提供方登记({
        'id':标识,
        'description':说明,
        'methods':[{
            'name':方法,
            'description':说明,
            'inputSchema':输入模式,
            'outputSchema':输出模式,
        }],
    },查询)
