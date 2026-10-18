'按调用方给的模式库惰性组装生成的远程定义。不登记、不传输'
__all__=['创建远程信息','是否远程方法']

def 取(主体,键):
    'dict 用键，对象用属性。缺则 None'
    if isinstance(主体,dict):
        if 键 not in 主体:
            return None
        return 主体[键]
    return getattr(主体,键,None)

def 有(主体,键):
    '键或属性在不在'
    if 主体 is None:
        return False
    if isinstance(主体,dict):
        return 键 in 主体
    return hasattr(主体,键)

def 创建远程信息(规格,模式库):
    '留下每个端点的一份生成定义。第一次访问才建描述符和方法索引；输入模式只在被要时才建'
    return 远程信息(规格,模式库)

def 是否远程方法(描述符):
    '直接调用、严格结果，并且带 input 与 invoke，才是生成出来的直接方法'
    if 取(取(描述符,'invocation'),'kind')!='direct':
        return False
    if 取(取(描述符,'result'),'mode')!='strict':
        return False
    if not callable(取(描述符,'input')):
        return False
    if not callable(取(描述符,'invoke')):
        return False
    return True

def 是否可选(参数):
    'json 来源且接受缺席时，线路字段可以不出现'
    return 取(参数,'source')=='json' and 取(参数,'acceptsUndefined') is True

def 复制参数(参数):
    '拷贝参数并把缺席的 wire 补成 name'
    副本=dict(参数)
    if not 有(副本,'wire') or 副本['wire'] is None:
        副本['wire']=副本['name']
    return 副本

def 读创建(编解码):
    '取出编解码上的 create，不调用'
    if isinstance(编解码,dict):
        return 编解码['create']
    return 编解码.create

def 读模式(编解码,键):
    '读取编解码上的模式字段'
    return 取(编解码,键)

class 远程信息:
    '调用方给的规格与模式库。描述符和方法索引在第一次访问时建好后复用'
    def __init__(自身,规格,模式库):
        '只保存规格和模式库，不在构造时建解析器'
        自身._规格=规格
        自身._模式库=模式库
        自身._索引=None

    @property
    def package(自身):
        '包名'
        return 自身._规格['package']

    @property
    def descriptors(自身):
        '全部调用描述符'
        return 自身._解析()['descriptors']

    @property
    def methods(自身):
        '直接方法，键是端点'
        return 自身._解析()['methods']

    def _解析(自身):
        '建描述符列表和直接方法表。直接方法才挂 input 与 invoke'
        if 自身._索引 is not None:
            return 自身._索引
        描述符列表=[]
        方法表={}
        for 端点,定义 in 自身._规格['methods'].items():
            分隔=端点.find('/')
            命名空间=端点[:分隔]
            方法名=端点[分隔+1:]
            参数列表=[]
            for 参数 in 定义['parameters']:
                参数列表.append(复制参数(参数))
            结果=定义['result']
            if 有(结果,'description') and 取(结果,'description') is not None:
                结果对象=结果值(结果)
            else:
                结果对象=结果
            描述符=dict(定义)
            描述符['id']=自身._规格['package']+'#'+端点
            描述符['namespace']=命名空间
            描述符['method']=方法名
            描述符['parameters']=参数列表
            描述符['result']=结果对象
            if 取(定义['invocation'],'kind')=='direct':
                输入槽=[None,None]
                模式库=自身._模式库
                def 做输入(选项=None,参数列表=参数列表,输入槽=输入槽,模式库=模式库):
                    'strict 与非 strict 各缓存一份具名输入'
                    if isinstance(选项,dict):
                        严格=选项.get('strict') is True
                    elif 选项 is None:
                        严格=False
                    else:
                        严格=getattr(选项,'strict',None) is True
                    下标=1 if 严格 else 0
                    if 输入槽[下标] is None:
                        输入槽[下标]=具名输入(参数列表,严格,模式库)
                    return 输入槽[下标]
                def 做调用(远程,输入,信号=None,命名空间=命名空间,方法名=方法名,参数列表=参数列表,定义=定义):
                    '按线路名取参数，命名空间访问仍走网关挂载'
                    值列表=[]
                    for 参数 in 参数列表:
                        线路名=参数['wire']
                        if isinstance(输入,dict):
                            值列表.append(输入[线路名] if 线路名 in 输入 else None)
                        else:
                            值列表.append(getattr(输入,线路名,None))
                    if 有(定义,'cancellation') and 取(定义,'cancellation') is not None:
                        值列表.append(信号)
                    接收者=getattr(远程,命名空间)
                    调用=getattr(接收者,方法名)
                    return 调用(*值列表)
                描述符['input']=做输入
                描述符['invoke']=做调用
                方法表[端点]=描述符
            描述符列表.append(描述符)
        自身._索引={'descriptors':描述符列表,'methods':方法表}
        return 自身._索引

class 具名输入:
    '按线路名组装的对象模式。create 与 json 投影都只建一次'
    def __init__(自身,参数列表,严格,模式库):
        '保存参数、是否严格，以及调用方的模式库'
        自身._参数列表=参数列表
        自身._严格=严格
        自身._模式库=模式库
        自身._模式=None
        自身._投影=None

    def _编解码(自身,参数):
        '严格时用 strictCodec，否则用 codec'
        if 自身._严格:
            return 参数['strictCodec']
        return 参数['codec']

    def create(自身):
        '建严格对象模式。可选线路字段用 optional，其余用 nonoptional'
        if 自身._模式 is None:
            字段={}
            for 参数 in 自身._参数列表:
                值=读创建(自身._编解码(参数))()
                if 是否可选(参数):
                    字段[参数['wire']]=值.optional()
                else:
                    字段[参数['wire']]=值.nonoptional()
            自身._模式=自身._模式库.strictObject(字段)
        return 自身._模式

    @property
    def jsonSchema(自身):
        '投影出的 JSON Schema。表达不了时没有这份字段'
        return 取(自身._投影结果(),'jsonSchema')

    @property
    def jsonSchemaError(自身):
        '表达不了时的说明'
        return 取(自身._投影结果(),'jsonSchemaError')

    def _投影结果(自身):
        '有任一参数给不出 JSON Schema 时只留下错误'
        if 自身._投影 is not None:
            return 自身._投影
        for 参数 in 自身._参数列表:
            编解码=自身._编解码(参数)
            if 读模式(编解码,'jsonSchema') is None:
                错误=读模式(编解码,'jsonSchemaError')
                if 错误 is None:
                    错误='No JSON Schema for parameter '+参数['wire']
                自身._投影={'jsonSchemaError':错误}
                return 自身._投影
        属性表={}
        必需=[]
        for 参数 in 自身._参数列表:
            编解码=自身._编解码(参数)
            模式=dict(读模式(编解码,'jsonSchema'))
            if 有(参数,'description') and 取(参数,'description') is not None:
                模式['description']=取(参数,'description')
            属性表[参数['wire']]=模式
            if not 是否可选(参数):
                必需.append(参数['wire'])
        自身._投影={
            'jsonSchema':{
                'type':'object',
                'properties':属性表,
                'required':必需,
                'additionalProperties':False,
            },
        }
        return 自身._投影

class 结果值:
    '结果编解码。jsonSchema 在第一次读取时补上 description'
    def __init__(自身,规格):
        '保存原编解码，投影留到读取时'
        自身._规格=规格
        自身._投影=None

    @property
    def mode(自身):
        '模式'
        return 取(自身._规格,'mode')

    @property
    def typeSymbol(自身):
        '类型符号'
        return 取(自身._规格,'typeSymbol')

    @property
    def create(自身):
        '原编解码的 create'
        return 读创建(自身._规格)

    @property
    def decode(自身):
        '原编解码的 decode'
        return 取(自身._规格,'decode')

    @property
    def encode(自身):
        '原编解码的 encode'
        return 取(自身._规格,'encode')

    @property
    def description(自身):
        '说明'
        return 取(自身._规格,'description')

    @property
    def jsonSchemaError(自身):
        '原编解码的 JSON Schema 错误'
        return 取(自身._规格,'jsonSchemaError')

    @property
    def jsonSchema(自身):
        '有模式时把 description 写进拷贝'
        if 自身._投影 is None:
            模式=取(自身._规格,'jsonSchema')
            if 模式 is None:
                自身._投影={'value':None}
            else:
                副本=dict(模式)
                副本['description']=取(自身._规格,'description')
                自身._投影={'value':副本}
        return 自身._投影['value']
