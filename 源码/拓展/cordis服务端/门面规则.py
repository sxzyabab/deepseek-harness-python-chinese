import json,math
from ...依赖.cordis.上下文 import 是上下文
from ...内核.作用域 import 获取作用域
from ...内核.工具 import 定义工具,断言受支持json模式

__all__=[
    '宿主运行器错误','动态工具标记','上下文动词','定时器动词',
    '克隆json','沙箱定义工具','规范化处理函数','沙箱登记工具',
    '是否插件','受护插件','插件显示名','沙箱上下文',
]

#常量
动态工具标记=object()
模式类型=frozenset(('string','number','integer','boolean','null','object','array','json'))
合法类型文="'string' | 'number' | 'integer' | 'boolean' | 'null' | 'object' | 'array' | 'json'"
注解键=('description','title','default','examples')
返回预览上限=120
上下文动词=frozenset([
    '副作用','监听','监听一次','提供服务','超时','间隔','节流','防抖',
])
定时器动词=frozenset(['超时','间隔','节流','防抖'])

#工具
class 宿主运行器错误(Exception):
    """动态宿主运行器包的异常基类。"""

def 是否普通记录(值):
    """普通字典，拒绝子类与数组。"""
    return type(值) is dict

def 是否稠密普通数组(值):
    """普通列表且无额外自有属性。"""
    if type(值) is not list:
        return False
    额外=getattr(值,'__dict__',None)
    if 额外 is not None and len(额外)>0:
        return False
    return True

def 是否有限json数字(值):
    """有限 JSON 数字，排除布尔与负零。"""
    if isinstance(值,bool):
        return False
    if isinstance(值,int):
        return True
    if isinstance(值,float):
        return math.isfinite(值) and not (值==0.0 and math.copysign(1.0,值)<0)
    return False

def 断言模式容器键(值,路径):
    """模式记录只能有字符串键。"""
    for 键 in 值:
        if not isinstance(键,str):
            raise 宿主运行器错误(f'harness.defineTool {路径} 只能包含自有可枚举的字符串键')

def 克隆json(值,路径):
    """跨边界无损 JSON 克隆；path 带调用方错误前缀。"""
    祖先=set()
    根盒=[None]
    def 写入(去向,项):
        """把一项装到根、数组下标或对象键。"""
        种=去向['kind']
        if 种=='root':
            根盒[0]=项
            return
        if 种=='array':
            去向['target'][去向['index']]=项
            return
        去向['target'][去向['key']]=项
    def 拒绝(处):
        """教学拒绝非 JSON。"""
        raise 宿主运行器错误(
            f'{处} 必须是无损 JSON 数据（对象、数组、字符串、数字、布尔、null）——'
            '不能是类实例、函数、Map/Set、Date 或 undefined。请用需要的值构造普通对象，'
            '调用方不需要返回值时 `return null`。'
        )
    任务列表=[{'kind':'visit','value':值,'path':路径,'destination':{'kind':'root'}}]
    任务=任务列表.pop() if 任务列表 else None
    while 任务 is not None:
        if 任务['kind']=='leave':
            祖先.discard(id(任务['source']))
            任务=任务列表.pop() if 任务列表 else None
            continue
        if 任务['kind']=='array-item':
            源=任务['source']
            下标=任务['index']
            if 下标>=len(源):
                拒绝(任务['path'])
            任务列表.append({
                'kind':'visit',
                'value':源[下标],
                'path':f"{任务['path']}[{下标}]",
                'destination':{'kind':'array','target':任务['target'],'index':下标},
            })
            任务=任务列表.pop() if 任务列表 else None
            continue
        当前=任务['value']
        if 当前 is None or isinstance(当前,str) or isinstance(当前,bool):
            写入(任务['destination'],当前)
            任务=任务列表.pop() if 任务列表 else None
            continue
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):
            if not 是否有限json数字(当前):
                拒绝(任务['path'])
            写入(任务['destination'],当前)
            任务=任务列表.pop() if 任务列表 else None
            continue
        if not isinstance(当前,(dict,list)) or id(当前) in 祖先:
            拒绝(任务['path'])
        if isinstance(当前,list):
            if not 是否稠密普通数组(当前):
                拒绝(任务['path'])
            输出=[]
            写入(任务['destination'],输出)
            祖先.add(id(当前))
            任务列表.append({'kind':'leave','source':当前})
            下标=len(当前)-1
            while 下标>=0:
                任务列表.append({
                    'kind':'array-item',
                    'source':当前,
                    'index':下标,
                    'path':任务['path'],
                    'target':输出,
                })
                下标-=1
            任务=任务列表.pop() if 任务列表 else None
            continue
        if not 是否普通记录(当前):
            拒绝(任务['path'])
        for 键 in 当前:
            if not isinstance(键,str):
                拒绝(任务['path'])
        输出={}
        写入(任务['destination'],输出)
        祖先.add(id(当前))
        任务列表.append({'kind':'leave','source':当前})
        条目=list(当前.items())
        下标=len(条目)-1
        while 下标>=0:
            键,子值=条目[下标]
            任务列表.append({
                'kind':'visit',
                'value':子值,
                'path':f"{任务['path']}.{键}",
                'destination':{'kind':'object','target':输出,'key':键},
            })
            下标-=1
        任务=任务列表.pop() if 任务列表 else None
    return 根盒[0]

def 复制注解(值,输出,路径):
    """复制共享注解词。"""
    if 'description' in 值:
        输出['description']=值['description']
    if 'title' in 值:
        输出['title']=值['title']
    if 'default' in 值:
        输出['default']=克隆json(值['default'],f'harness.defineTool {路径}.default')
    if 'examples' in 值:
        输出['examples']=克隆json(值['examples'],f'harness.defineTool {路径}.examples')

def 断言模式键(值,路径,允许):
    """拒绝统一 DSL 会忽略的键。"""
    断言模式容器键(值,路径)
    for 键 in 值:
        if 键 not in 允许:
            raise 宿主运行器错误(f'harness.defineTool {路径}.{键} 不被统一 schema DSL 支持')

def 规范化必填名(值,属性表,路径):
    """校验 required 名并做成查找集。"""
    if 值 is None:
        return set()
    if not 是否稠密普通数组(值):
        raise 宿主运行器错误(f'harness.defineTool {路径} 必须是已声明属性名的数组')
    名集=set()
    下标=0
    while 下标<len(值):
        名=值[下标]
        if not isinstance(名,str):
            raise 宿主运行器错误(f'harness.defineTool {路径} 必须是已声明属性名的数组')
        名集.add(名)
        if 名 not in 属性表:
            文=json.dumps(名,ensure_ascii=False,separators=(',',':'),allow_nan=False)
            raise 宿主运行器错误(f'harness.defineTool {路径} 点名了未声明属性 {文}')
        下标+=1
    return 名集

def 写入规范化值(去向,值):
    """安装一个规范化节点。"""
    种=去向['kind']
    if 种=='property':
        去向['target'][去向['key']]=值
    elif 种=='item':
        去向['target']['items']=值
    else:
        去向['target'][去向['index']]=值

def 写入规范化表(去向,值):
    """安装一个规范化属性表。"""
    if 去向['kind']=='root':
        去向['holder']['value']=值
    else:
        去向['target']['properties']=值

def 规范化属性表(条目,路径,必填名,原始):
    """规范化隐式属性表及其后代。"""
    持有={}
    祖先=set()
    任务列表=[{
        'kind':'map',
        'entries':条目,
        'path':路径,
        'requiredNames':必填名,
        'raw':原始,
        'destination':{'kind':'root','holder':持有},
    }]
    任务=任务列表.pop() if 任务列表 else None
    while 任务 is not None:
        if 任务['kind']=='leave':
            祖先.discard(id(任务['value']))
            任务=任务列表.pop() if 任务列表 else None
            continue
        if 任务['kind']=='map':
            if id(任务['entries']) in 祖先:
                raise 宿主运行器错误(f"harness.defineTool {任务['path']} 存在循环")
            断言模式容器键(任务['entries'],任务['path'])
            祖先.add(id(任务['entries']))
            规格={}
            写入规范化表(任务['destination'],规格)
            任务列表.append({'kind':'leave','value':任务['entries']})
            表项=list(任务['entries'].items())
            下标=len(表项)-1
            while 下标>=0:
                键,子值=表项[下标]
                任务列表.append({
                    'kind':'value',
                    'value':子值,
                    'path':f"{任务['path']}.{键}",
                    'forceRequired':键 in 任务['requiredNames'],
                    'raw':任务['raw'],
                    'parameterProperty':True,
                    'destination':{'kind':'property','target':规格,'key':键},
                })
                下标-=1
            任务=任务列表.pop() if 任务列表 else None
            continue
        值=任务['value']
        路径=任务['path']
        if not 是否普通记录(值):
            raise 宿主运行器错误(f'harness.defineTool {路径} 必须是 ParameterSchemaSpec 属性对象')
        断言模式容器键(值,路径)
        if id(值) in 祖先:
            raise 宿主运行器错误(f'harness.defineTool {路径} 存在循环')
        祖先.add(id(值))
        必填键=('required',) if 任务['parameterProperty'] and not 任务['raw'] else ()
        if 任务['parameterProperty'] and 任务['raw'] and 'required' in 值 and 值.get('type')!='object':
            raise 宿主运行器错误(f'harness.defineTool {路径}.required 属于外层原始 object schema')
        if 任务['parameterProperty'] and not 任务['raw'] and 'required' in 值 and 值['required'] is not True:
            raise 宿主运行器错误(f'harness.defineTool {路径}.required 若出现则必须为 true')
        属性={}
        写入规范化值(任务['destination'],属性)
        任务列表.append({'kind':'leave','value':值})
        if 任务['forceRequired'] or 值.get('required') is True:
            属性['required']=True
        复制注解(值,属性,路径)
        if 'oneOf' in 值:
            断言模式键(值,路径,('oneOf',)+必填键+注解键)
            if not 是否稠密普通数组(值['oneOf']) or len(值['oneOf'])<2:
                raise 宿主运行器错误(f'harness.defineTool {路径}.oneOf 至少要有两支 schema')
            联合=[]
            属性['oneOf']=联合
            下标=len(值['oneOf'])-1
            while 下标>=0:
                任务列表.append({
                    'kind':'value',
                    'value':值['oneOf'][下标],
                    'path':f'{路径}.oneOf[{下标}]',
                    'forceRequired':False,
                    'raw':任务['raw'],
                    'parameterProperty':False,
                    'destination':{'kind':'one-of','target':联合,'index':下标},
                })
                下标-=1
            任务=任务列表.pop() if 任务列表 else None
            continue
        if 任务['raw'] and 'type' not in 值:
            断言模式键(值,路径,注解键)
            属性['type']='json'
            任务=任务列表.pop() if 任务列表 else None
            continue
        if 值.get('type') not in 模式类型 or (任务['raw'] and 值.get('type')=='json'):
            文=json.dumps(值.get('type'),ensure_ascii=False,separators=(',',':'),allow_nan=False)
            raise 宿主运行器错误(f'harness.defineTool {路径} 必须声明合法 type: {合法类型文}（得到 {文}）')
        类型名=值['type']
        属性['type']=类型名
        if 类型名=='object':
            允许=('type','properties','additionalProperties')+必填键
            if 任务['raw']:
                允许=允许+('required',)
            断言模式键(值,路径,允许+注解键)
            if not 任务['raw'] and ('additionalProperties' not in 值 or not isinstance(值['additionalProperties'],bool)):
                raise 宿主运行器错误(f'harness.defineTool {路径}.additionalProperties 必须显式为 true 或 false')
            if 任务['raw'] and 'additionalProperties' in 值 and not isinstance(值['additionalProperties'],bool):
                raise 宿主运行器错误(f'harness.defineTool {路径}.additionalProperties 必须是布尔')
            if 任务['raw'] and 'required' in 值 and 值['required'] is None:
                raise 宿主运行器错误(f'harness.defineTool {路径}.required 必须是已声明属性名的数组')
            if 任务['raw']:
                属性['additionalProperties']=值['additionalProperties'] if 'additionalProperties' in 值 else True
            else:
                属性['additionalProperties']=值['additionalProperties']
            if 'properties' in 值:
                属性表=值['properties']
                if not 是否普通记录(属性表):
                    raise 宿主运行器错误(f'harness.defineTool {路径}.properties 必须是 schema 对象表')
                if 任务['raw']:
                    嵌套必填=规范化必填名(值.get('required'),属性表,f'{路径}.required')
                else:
                    嵌套必填=set()
                任务列表.append({
                    'kind':'map',
                    'entries':属性表,
                    'path':f'{路径}.properties',
                    'requiredNames':嵌套必填,
                    'raw':任务['raw'],
                    'destination':{'kind':'properties','target':属性},
                })
            elif 任务['raw'] and 值.get('required') is not None:
                规范化必填名(值['required'],{},f'{路径}.required')
        elif 类型名=='array':
            断言模式键(值,路径,('type','items')+必填键+注解键)
            if 'items' in 值:
                任务列表.append({
                    'kind':'value',
                    'value':值['items'],
                    'path':f'{路径}.items',
                    'forceRequired':False,
                    'raw':任务['raw'],
                    'parameterProperty':False,
                    'destination':{'kind':'item','target':属性},
                })
        elif 类型名 in ('string','number','integer','boolean','null'):
            断言模式键(值,路径,('type','enum','const')+必填键+注解键)
            if 'enum' in 值:
                if not 是否稠密普通数组(值['enum']) or len(值['enum'])==0:
                    raise 宿主运行器错误(f'harness.defineTool {路径}.enum 必须是非空数组')
                属性['enum']=克隆json(值['enum'],f'harness.defineTool {路径}.enum')
            if 'const' in 值:
                属性['const']=克隆json(值['const'],f'harness.defineTool {路径}.const')
        elif 类型名=='json':
            断言模式键(值,路径,('type',)+必填键+注解键)
        else:
            raise 宿主运行器错误(f'harness.defineTool {路径} 必须声明合法 type: {合法类型文}')
        任务=任务列表.pop() if 任务列表 else None
    return 持有['value'] if 'value' in 持有 else {}

def 规范化参数模式规格(值,路径='parameters'):
    """把沙箱 parameters 收成宿主 ParameterSchemaSpec。"""
    if not 是否普通记录(值):
        raise 宿主运行器错误(f'harness.defineTool {路径} 必须是 ParameterSchemaSpec 对象')
    if 值.get('type')=='object':
        断言模式键(值,路径,('type','properties','required','additionalProperties')+注解键)
        if not 是否普通记录(值.get('properties')):
            raise 宿主运行器错误(f'harness.defineTool {路径}.properties 必须是 schema 对象表')
        if 'additionalProperties' in 值 and 值['additionalProperties'] is not True:
            raise 宿主运行器错误(f'harness.defineTool {路径}.additionalProperties 必须为 true 或省略，因为隐式参数根是开放的')
        if 'required' in 值 and 值['required'] is None:
            raise 宿主运行器错误(f'harness.defineTool {路径}.required 必须是已声明属性名的数组')
        必填=规范化必填名(值.get('required'),值['properties'],f'{路径}.required')
        根注解={}
        复制注解(值,根注解,路径)
        出={'spec':规范化属性表(值['properties'],路径,必填,True)}
        if len(根注解)>0:
            出['rootAnnotations']=根注解
        return 出
    return {'spec':规范化属性表(值,路径,set(),False)}

def 标记动态工具(工具):
    """钉上动态工具标记。"""
    工具[动态工具标记]=True
    return 工具

def 断言动态工具(工具):
    """必须是 harness.defineTool 的返回。"""
    if not 是否普通记录(工具) or 工具.get(动态工具标记) is not True:
        raise 宿主运行器错误('动态工具登记必须使用 harness.defineTool(...) 返回的工具')

def 是否内容块形态(值):
    """带字符串 type 的普通对象。"""
    return 是否普通记录(值) and isinstance(值.get('type'),str)

def 描述返回(值):
    """非法 execute 返回的紧凑 JSON 预览。"""
    文本=json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    数据=文本.encode('utf-8')
    if len(数据)<=返回预览上限:
        return 文本
    切=数据[:返回预览上限]
    while True:
        try:
            return 切.decode('utf-8')+'…'
        except UnicodeDecodeError:
            切=切[:-1]

def 断言已渲染内容(值):
    """校验并交出内容块列表。"""
    if isinstance(值,list) and all(是否内容块形态(项) for 项 in 值):
        return 值
    raise 宿主运行器错误(
        f'output.render 返回了 {描述返回(值)} —— 必须返回内容块数组：\n'
        "  ✓ return [{ type: 'text', text: String(value) }]"
    )

#
def 沙箱定义工具(选项):
    """交给沙箱的 harness.defineTool：规范化 parameters 与 execute 返回。"""
    if not 是否普通记录(选项):
        raise 宿主运行器错误('harness.defineTool options 必须是对象')
    规范化=规范化参数模式规格(选项.get('parameters'))
    if not 是否普通记录(选项.get('output')):
        raise 宿主运行器错误('harness.defineTool output 必须声明 { schema, render, presentationMeta? }')
    输出=选项['output']
    if not callable(输出.get('render')):
        raise 宿主运行器错误('harness.defineTool output.render 必须是函数')
    if 输出.get('presentationMeta') is not None and not callable(输出.get('presentationMeta')):
        raise 宿主运行器错误('harness.defineTool output.presentationMeta 若出现则必须是函数')
    if not callable(选项.get('execute')):
        raise 宿主运行器错误('harness.defineTool execute 必须是函数')
    模式=克隆json(输出['schema'],'harness.defineTool output.schema')
    原始执行=选项['execute']
    原始渲染=输出['render']
    原始呈现=输出.get('presentationMeta')
    输出体={'schema':模式}
    def 渲染(参数,值):
        """克隆并收窄内容块。"""
        return 断言已渲染内容(克隆json(原始渲染(参数,值),'harness.defineTool output.render result'))
    输出体['render']=渲染
    if 原始呈现 is not None:
        def 呈现元数据(参数,值):
            """克隆呈现元数据。"""
            return 克隆json(原始呈现(参数,值),'harness.defineTool output.presentationMeta result')
        输出体['presentationMeta']=呈现元数据
    def 执行(参数,执行上下文):
        """克隆 execute 返回。"""
        return 克隆json(原始执行(参数,执行上下文),'harness.defineTool execute result')
    工具=定义工具({
        **选项,
        'parameters':规范化['spec'],
        'output':输出体,
        'execute':执行,
    })
    参数={**工具['parameters']}
    if 'rootAnnotations' in 规范化:
        参数={**参数,**规范化['rootAnnotations']}
    断言受支持json模式(参数)
    return 标记动态工具({**工具,'parameters':参数})

def 规范化处理函数(方法,函数):
    """规范化 harness.handle 登记。"""
    if not isinstance(方法,str) or 方法=='':
        raise 宿主运行器错误('harness.handle(method, fn) 需要非空的方法名字符串')
    if not callable(函数):
        raise 宿主运行器错误(f'harness.handle("{方法}") 的第二个参数必须是处理函数')
    def 处理(参数):
        """克隆处理结果。"""
        return 克隆json(函数(参数),f'harness.handle("{方法}") result')
    return {'method':方法,'handler':处理}

def 沙箱登记工具(上下文,工具):
    """在真实 tools 服务上登记已标记的动态工具。"""
    断言动态工具(工具)
    return 上下文.tools.登记(工具)

def 拒绝门面(报告失败,消息):
    """先报告再抛同一份错误。"""
    错误=宿主运行器错误(消息)
    报告失败(错误)
    raise 错误

def 拒绝上下文返回(值,服务名,报告失败):
    """服务返回 Context 则教学拒绝。"""
    if 值 is None or isinstance(值,(str,bytes,bool,int,float,dict,list,tuple,set)):
        return 值
    if 是上下文(值):
        return 拒绝门面(
            报告失败,
            f'服务 "{服务名}" 返回了 cordis Context，沙箱不暴露它。'
            '请通过自己的插件 ctx（ctx.监听 / ctx.提供服务 / ctx.tools.登记）'
            '和已注入的服务操作，不要拿另一份上下文。',
        )
    return 值

class 受护服务:
    """方法转发后的返回值再过 Context 拒绝。"""
    def __init__(自身,服务,名,报告失败):
        """钉死真实服务。"""
        object.__setattr__(自身,'_服务',服务)
        object.__setattr__(自身,'_名',名)
        object.__setattr__(自身,'_报告失败',报告失败)

    def __call__(自身,*位置参数):
        """可调用服务本身。"""
        结果=自身._服务(*位置参数)
        return 拒绝上下文返回(结果,自身._名,自身._报告失败)

    def __getattr__(自身,属性):
        """读成员；函数包装后再拒绝 Context。"""
        值=getattr(自身._服务,属性)
        if callable(值):
            def 转发(*位置参数):
                """转发并拒绝 Context 返回。"""
                结果=值(*位置参数)
                return 拒绝上下文返回(结果,自身._名,自身._报告失败)
            return 转发
        return 拒绝上下文返回(值,自身._名,自身._报告失败)

class 沙箱工具座位:
    """登记受标记工具；schemas/get 只给只读投影。"""
    def __init__(自身,上下文):
        """钉死真实上下文。"""
        自身._上下文=上下文

    def 登记(自身,工具):
        """登记动态工具。"""
        return 沙箱登记工具(自身._上下文,工具)

    def 诸模式(自身):
        """作用域可见的模式投影。"""
        return 自身._上下文.tools.诸模式(获取作用域(自身._上下文))

    def 获取(自身,名):
        """按名取模式视图，不交活定义。"""
        for 项 in 自身.诸模式():
            if 项.get('name')==名:
                return 项
        return None

def 已声明注入(上下文):
    """fiber.inject 的服务名集。"""
    表=上下文.纤程.依赖表
    return set(表) if 表 is not None else set()

class 动态宿主上下文:
    """运行中宿主半看到的白名单 ctx。"""
    def __init__(自身,真实,报告失败):
        """钉死真实上下文与失败报告。"""
        object.__setattr__(自身,'_真实',真实)
        object.__setattr__(自身,'_报告失败',报告失败)
        object.__setattr__(自身,'_已声明',已声明注入(真实))
        object.__setattr__(自身,'_工具',沙箱工具座位(真实))

    def 获取服务(自身,名):
        """可选查找，不要求声明。"""
        return 自身._读服务(名,False)

    def _拒绝读取(自身,属性):
        """未声明服务与框架内部分教学。"""
        if 自身._真实.获取服务(属性,False) is not None:
            return 拒绝门面(
                自身._报告失败,
                f'服务 "{属性}" 未注入。请在插件上声明 inject: [\'{属性}\', …]，'
                '这样提供方卸载时 cordis 会停放该动态包。',
            )
        return 拒绝门面(
            自身._报告失败,
            f'沙箱 ctx 不暴露 "{属性}"。可用：ctx.tools.登记 / ctx.监听 / ctx.提供服务 / '
            '注入 timer 后的定时器助手，以及 inject 里声明的服务。'
            '框架内部（root、fiber、registry、extend、plugin 等）按设计不外露。',
        )

    def _读服务(自身,名,须声明):
        """tools 走座位；其余过 Context 拒绝。"""
        if 名=='tools':
            return 自身._工具
        if 须声明 and 名 not in 自身._已声明:
            return 自身._拒绝读取(名)
        服务=拒绝上下文返回(自身._真实.获取服务(名,False),名,自身._报告失败)
        if 服务 is None:
            return 服务
        if not isinstance(服务,(dict,list)) and not callable(服务) and not hasattr(服务,'__dict__'):
            return 服务
        return 受护服务(服务,名,自身._报告失败)

    def __getattr__(自身,属性):
        """tools / 获取服务 / 白名单动词 / 已声明服务。"""
        if 属性=='tools':
            return 自身._工具
        if 属性=='获取服务':
            return 自身.获取服务
        if 属性 in 上下文动词:
            def 转发(*位置参数):
                """惰性转发白名单动词。"""
                if 属性 in 定时器动词 and 'timer' not in 自身._已声明:
                    return 自身._拒绝读取('timer')
                方法=getattr(自身._真实,属性)
                return 方法(*位置参数)
            return 转发
        return 自身._读服务(属性,True)

    def __setattr__(自身,属性,值):
        """只读。"""
        拒绝门面(自身._报告失败,f'沙箱 ctx 只读，不能赋值 "{属性}"')

    def __contains__(自身,属性):
        """可见性：座位、动词（定时器须已声明 timer）、已声明服务。"""
        if 属性=='tools' or 属性=='获取服务':
            return True
        if not isinstance(属性,str):
            return False
        if 属性 in 上下文动词:
            if 属性 in 定时器动词 and 'timer' not in 自身._已声明:
                return False
            return True
        return 属性 in 自身._已声明

def 沙箱上下文(上下文,报告失败):
    """构造运行中宿主半的门面。"""
    return 动态宿主上下文(上下文,报告失败)

def 是否插件(值):
    """函数，或带 apply 的对象。"""
    if callable(值):
        return True
    if isinstance(值,dict):
        return callable(值.get('apply'))
    return 值 is not None and callable(getattr(值,'apply',None))

def 受护插件(插件,报告失败):
    """apply 收到沙箱上下文，并尽量保留 inject。"""
    if callable(插件) and not isinstance(插件,dict):
        def 应用(上下文,配置=None):
            """函数插件走门面。"""
            return 插件(沙箱上下文(上下文,报告失败),配置)
        return {'name':插件显示名(插件),'apply':应用}
    入口=插件['apply'] if isinstance(插件,dict) else 插件.apply
    def 应用(上下文,配置=None):
        """对象插件走门面。"""
        return 入口(沙箱上下文(上下文,报告失败),配置)
    if isinstance(插件,dict):
        出=dict(插件)
        出['apply']=应用
        return 出
    出={'apply':应用}
    for 名 in ('name','inject','Config'):
        if hasattr(插件,名):
            出[名]=getattr(插件,名)
    return 出

def 插件显示名(插件):
    """运行结果与巡检用的显示名。"""
    if isinstance(插件,dict):
        名=插件.get('name')
    else:
        名=getattr(插件,'name',None)
    if isinstance(名,str) and 名!='':
        return 名
    备用=getattr(插件,'__name__',None)
    if isinstance(备用,str) and 备用!='':
        return 备用
    return '<匿名>'
