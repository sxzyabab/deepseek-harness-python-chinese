__all__=[#公开
    '是追加面事件','是替换面事件','上下文出处','上下文形态',
    '空助手块','转助手块','转助手块列表','是令牌增量','展示失败文案',
]#公开结束

def 事件面(事件):
    """读 surface，缺席则看 data.surface。"""
    if 'surface' in 事件:
        return 事件['surface']#顶层面
    if 'data' not in 事件:
        return None#无载荷
    数据=事件['data']#载荷
    if 数据 is None or 'surface' not in 数据:
        return None#无嵌套面
    return 数据['surface']#嵌套

def 是追加面事件(事件):
    """surface==append 或缺省视为追加。"""
    return 事件面(事件) in (None,'append','append-surface')#追加

def 是替换面事件(事件):
    """surface==replace / replacement。"""
    return 事件面(事件) in ('replace','replacement','replace-surface')#替换

def 上下文出处(来源):
    """从持久化来源投影 provenance。来源为 dict。"""
    种=来源['kind'] if 'kind' in 来源 else None#种类
    if 种=='user':
        return {'role':'user','producer':'user'}#用户
    if 种=='plugin':
        插件=来源['plugin'] if 'plugin' in 来源 else None#插件名
        return {'role':'context','producer':插件 if 插件 is not None and 插件!='' else 'plugin'}#插件名
    return {'role':'context','producer':str(种) if 种 is not None else 'unknown'}#其它

def 上下文形态(来源):
    """有 form 则原样，否则 generic。"""
    if 'form' not in 来源:
        return 'generic'#缺省
    形=来源['form']#形态
    return 形 if 形 is not None else 'generic'#缺省

def 空助手块(块种):
    """按块种类造空底座。"""
    if 块种=='text':
        return {'kind':'text','text':''}#空文本
    if 块种=='reasoning':
        return {'kind':'reasoning','text':''}#空推理
    if 块种=='tool-call':
        return {'kind':'tool-call','callId':'','name':'','argsRaw':''}#空工具
    return {'kind':块种}#其它

def 转助手块(块):
    """统一 kind 字段。块为 dict。"""
    if 'kind' in 块:
        return 块#原样
    种=块['type'] if 'type' in 块 else None#type → kind
    if 种=='text':
        return {'kind':'text','text':块['text'] if 'text' in 块 else ''}#文本
    if 种=='reasoning':
        return {'kind':'reasoning','text':块['text'] if 'text' in 块 else ''}#推理
    if 种=='tool-call':
        if 'id' in 块:
            调用=str(块['id'])#id
        elif 'callId' in 块:
            调用=str(块['callId'])#callId
        else:
            调用=''#空
        if 'arguments' in 块:
            参数=块['arguments']#arguments
        elif 'argsRaw' in 块:
            参数=块['argsRaw']#argsRaw
        else:
            参数=''#空
        return {'kind':'tool-call','callId':调用,'name':块['name'] if 'name' in 块 else '','argsRaw':参数}#工具
    其余={键:值 for 键,值 in 块.items() if 键!='type'}#去掉 type
    其余['kind']=种#写入 kind
    return 其余#其它

def 转助手块列表(内容):
    """内容块数组 → 助手块数组。"""
    if 内容 is None or len(内容)==0:
        return []#空
    return [转助手块(块) for 块 in 内容]#逐块

def 是令牌增量(块):
    """text-delta / reasoning-delta。"""
    种=块['type'] if 'type' in 块 else None#种
    return 种 in ('text-delta','reasoning-delta')#增量

def 展示失败文案(失败):
    """优先 message，其次 code，再次 str。失败为 dict。"""
    if 失败 is None:
        return ''#空
    if 'message' in 失败 and 失败['message'] is not None and 失败['message']!='':
        return str(失败['message'])#文
    if 'code' in 失败 and 失败['code'] is not None and 失败['code']!='':
        return str(失败['code'])#码
    return str(失败)#兜底
