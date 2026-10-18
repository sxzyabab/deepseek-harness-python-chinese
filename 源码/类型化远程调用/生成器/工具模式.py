'把已解析类型无损投影成工具模式子集'
__all__=['工具模式错误','投影工具模式']

class 工具模式错误(Exception):
    '工具模式子集不能在不放宽约束的情况下表示这个类型'
    name='ToolSchemaError'
    def __init__(自身,消息=''):
        '保存说明'
        super().__init__(消息)

def 同值(左,右):
    '1 与 True 不是同一个字面量'
    if type(左) is not type(右):
        return False
    return 左==右

def 含有(值列表,值):
    '值列表里有没有同一个字面量'
    for 已见 in 值列表:
        if 同值(已见,值):
            return True
    return False

def 去重(值列表):
    '按出现顺序去掉重复字面量'
    结果=[]
    for 值 in 值列表:
        if not 含有(结果,值):
            结果.append(值)
    return 结果

def 字面量值(模式):
    'const 或 enum。都没有则 None。const 为 null 也算有值'
    if 'const' in 模式:
        return [模式['const']]
    if 'enum' in 模式:
        return 模式['enum']
    return None

def 是大整数(节点):
    'Python 没有 bigint。字面量文本以 n 结尾的整数，以及非 JSON 标量，都按 bigint 拒绝'
    值=节点['value'] if 'value' in 节点 else None
    if type(值).__name__=='bigint':
        return True
    文本=节点['text'] if 'text' in 节点 else ''
    if isinstance(值,bool) or isinstance(值,str) or isinstance(值,float) or 值 is None:
        return False
    if isinstance(值,int):
        return isinstance(文本,str) and 文本.endswith('n')
    return True

def 标量类型(值):
    'JSON 标量的 type 名'
    if 值 is None:
        return 'null'
    if isinstance(值,bool):
        return 'boolean'
    if isinstance(值,str):
        return 'string'
    return 'number'

def 不相交(左,右):
    '两边没有必填且字面量互斥的判别字段时，视为相交'
    if 'oneOf' in 左 and 左['oneOf'] is not None:
        for 分支 in 左['oneOf']:
            if not 不相交(分支,右):
                return False
        return True
    if 'oneOf' in 右 and 右['oneOf'] is not None:
        for 分支 in 右['oneOf']:
            if not 不相交(左,分支):
                return False
        return True
    左类型=左['type'] if 'type' in 左 else None
    右类型=右['type'] if 'type' in 右 else None
    if 左类型!=右类型:
        return 左类型 is not None and 右类型 is not None
    if 左类型!='object' or 右类型!='object':
        return False
    左必需=左['required'] if 'required' in 左 and 左['required'] is not None else []
    右必需=右['required'] if 'required' in 右 and 右['required'] is not None else []
    左属性=左['properties'] if 'properties' in 左 else None
    右属性=右['properties'] if 'properties' in 右 else None
    for 名 in 左必需:
        if 名 not in 右必需:
            continue
        if not isinstance(左属性,dict) or not isinstance(右属性,dict):
            continue
        if 名 not in 左属性 or 名 not in 右属性:
            continue
        第一=字面量值(左属性[名])
        第二=字面量值(右属性[名])
        if 第一 is None or 第二 is None:
            continue
        互斥=True
        for 值 in 第一:
            if 含有(第二,值):
                互斥=False
                break
        if 互斥:
            return True
    return False

def 投影工具模式(渲染器,类型,封闭对象=False,可选=False):
    '把一个已解析类型投影成工具模式。表达不了且不能不放宽约束时抛工具模式错误，调用方把它当成没有投影。封闭对象为真时，声明的请求对象写 additionalProperties false。可选取消顶层由可选参数带来的 undefined'
    活跃=set()

    def 失败(主语):
        '表达不了'
        raise 工具模式错误('typert tool schema: '+主语)

    def 对象(成员列表):
        '公开实例属性收成对象。索引签名要求字符串键和不约束的 JSON 值'
        属性表={}
        必需=[]
        有索引=False
        for 成员 in 成员列表:
            if 成员.get('static') or 成员.get('visibility')!='public' or 成员.get('computed')=='symbol':
                continue
            if 成员.get('kind')=='index':
                签名=成员['signature']
                参数列表=签名['parameters'] if 'parameters' in 签名 else []
                if len(参数列表)==0:
                    失败('selected dictionaries require string keys and unconstrained JSON values')
                键模式=投影(参数列表[0]['type'])
                返回模式=投影(签名['returns'])
                if 键模式.get('type')!='string' or len(返回模式)!=0:
                    失败('selected dictionaries require string keys and unconstrained JSON values')
                有索引=True
                continue
            if 成员.get('kind')!='property' or 成员.get('computed')=='dynamic':
                失败('unsupported member '+str(成员.get('name')))
            if 'jsonName' in 成员 and 成员['jsonName'] is not None:
                名=成员['jsonName']
            else:
                名=成员['name']
            模式=投影(成员['type'],成员.get('optional') is True)
            if 'description' in 成员 and 成员['description'] is not None:
                带说明=dict(模式)
                带说明['description']=成员['description']
                属性表[名]=带说明
            else:
                属性表[名]=模式
            if not 成员.get('optional'):
                必需.append(名)
        return {
            'type':'object',
            'properties':属性表,
            'required':必需,
            'additionalProperties':有索引 or not 封闭对象,
        }

    def 联合(输入):
        '空模式吞掉整个联合。同 type 的标量合并字面量。分支相交或没有必填判别字段则失败'
        for 分支 in 输入:
            if len(分支)==0:
                return {}
        分支列表=[]
        for 分支 in 输入:
            标量='type' in 分支 and 分支['type'] not in ('object','array')
            先前=None
            if 标量:
                for 候选 in 分支列表:
                    if ('type' in 候选 and 'type' in 分支 and 候选['type']==分支['type']) or ('type' not in 候选 and 'type' not in 分支):
                        先前=候选
                        break
            if 先前 is None:
                分支列表.append(分支)
                continue
            已有值=字面量值(先前)
            新值=字面量值(分支)
            if 已有值 is None or 新值 is None:
                if 'const' in 先前:
                    del 先前['const']
                if 'enum' in 先前:
                    del 先前['enum']
            else:
                if 'const' in 先前:
                    del 先前['const']
                先前['enum']=去重(list(已有值)+list(新值))
        if len(分支列表)==1:
            return 分支列表[0]
        if len(分支列表)==0:
            失败('empty selected union')
        下标=0
        while 下标<len(分支列表):
            右起=下标+1
            while 右起<len(分支列表):
                if not 不相交(分支列表[下标],分支列表[右起]):
                    失败('selected union branches overlap or have no required discriminator')
                右起=右起+1
            下标=下标+1
        return {'oneOf':分支列表}

    def 投影(标识,是否省略=False):
        '按节点种类投影。环上的类型必须已经声明为 JSON 值'
        节点=渲染器.node(标识)
        if 节点.get('json'):
            return {}
        if 标识 in 活跃:
            失败('recursive selected type requires a supported JSON value declaration')
        活跃.add(标识)
        try:
            种类=节点['kind']
            if 种类=='keyword':
                if 节点['name'] in ('string','number','boolean'):
                    return {'type':节点['name']}
                失败('unsupported '+节点['name']+' value')
            if 种类=='literal':
                if 是大整数(节点):
                    失败('bigint is not JSON')
                值=节点['value'] if 'value' in 节点 else None
                return {'type':标量类型(值),'const':值}
            if 种类=='parenthesized':
                return 投影(节点['type'],是否省略)
            if 种类=='array':
                return {'type':'array','items':投影(节点['element'])}
            if 种类=='object':
                return 对象(节点['members'])
            if 种类=='reference':
                目标=节点['target']
                if 目标['kind']!='declaration' or len(节点['arguments'])!=0:
                    失败('unsupported selected reference '+节点['name'])
                声明=渲染器.declaration(目标['symbol'])
                if 声明.get('kind')=='alias' and 'type' in 声明 and 声明['type'] is not None:
                    模式=投影(声明['type'],是否省略)
                else:
                    模式=对象(声明['members'])
                继承=声明['extends'] if 'extends' in 声明 and 声明['extends'] is not None else []
                if len(继承)>0:
                    失败('unresolved inherited selected type')
                if 'description' in 声明 and 声明['description'] is not None:
                    带说明=dict(模式)
                    带说明['description']=声明['description']
                    return 带说明
                return 模式
            if 种类=='union':
                留下=[]
                for 项 in 节点['types']:
                    分支=渲染器.node(项)
                    if 是否省略 and 分支.get('kind')=='keyword' and 分支.get('name')=='undefined':
                        continue
                    留下.append(项)
                投影列表=[]
                for 项 in 留下:
                    投影列表.append(投影(项))
                return 联合(投影列表)
            失败('unsupported selected '+种类+' type')
        finally:
            活跃.discard(标识)

    return 投影(类型,可选)
