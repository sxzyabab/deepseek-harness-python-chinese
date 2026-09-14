__all__=[#公开
    '是追加面事件','是替换面事件','上下文出处','上下文形态',
    '空助手块','转助手块','转助手块列表','是令牌增量','展示失败文案',
]#公开结束

def 是追加面事件(事件):#是否追加面
    """surface==append 或缺省视为追加。"""
    面=事件['surface'] if 'surface' in 事件 else None#面
    if 面 is None and 'data' in 事件:#嵌套
        数据=事件['data']#载荷
        面=数据['surface'] if 数据 is not None and 'surface' in 数据 else None#嵌套
    return 面 in (None,'append','append-surface')#追加

def 是替换面事件(事件):#是否替换面
    """surface==replace / replacement。"""
    面=事件['surface'] if 'surface' in 事件 else None#面
    if 面 is None and 'data' in 事件:#嵌套
        数据=事件['data']#载荷
        面=数据['surface'] if 数据 is not None and 'surface' in 数据 else None#嵌套
    return 面 in ('replace','replacement','replace-surface')#替换

def 上下文出处(来源):#角色与生产者名
    """从持久化来源投影 provenance。"""
    种=来源['kind'] if 'kind' in 来源 else None#种类
    if 种=='user':#用户
        return {'role':'user','producer':'user'}#用户
    if 种=='plugin':#插件
        插件=来源['plugin'] if 'plugin' in 来源 else None#插件名
        return {'role':'context','producer':插件 if 插件 is not None else 'plugin'}#插件名
    return {'role':'context','producer':str(种 if 种 is not None else 'unknown')}#其它

def 上下文形态(来源):#生产者声明的信息形态
    """有 form 则原样，否则 generic。"""
    形=来源['form'] if 'form' in 来源 else None#形态
    return 形 if 形 is not None else 'generic'#缺省

def 空助手块(块种):#空助手块
    """按块种类造空底座。"""
    if 块种=='text':#文本
        return {'kind':'text','text':''}#空文本
    if 块种=='reasoning':#推理
        return {'kind':'reasoning','text':''}#空推理
    if 块种=='tool-call':#工具
        return {'kind':'tool-call','callId':'','name':'','argsRaw':''}#空工具
    return {'kind':块种}#其它

def 转助手块(块):#单块转换
    """统一 kind 字段。"""
    if 'kind' in 块:#已有
        return 块#原样
    种=块['type'] if 'type' in 块 else None#type → kind
    if 种=='text':#文本
        return {'kind':'text','text':块['text'] if 'text' in 块 else ''}#文本
    if 种=='reasoning':#推理
        return {'kind':'reasoning','text':块['text'] if 'text' in 块 else ''}#推理
    if 种=='tool-call':#工具
        调用=块['id'] if 'id' in 块 else (块['callId'] if 'callId' in 块 else '')#id
        参=块['arguments'] if 'arguments' in 块 else (块['argsRaw'] if 'argsRaw' in 块 else '')#参数
        return {'kind':'tool-call','callId':str(调用 if 调用 is not None else ''),'name':块['name'] if 'name' in 块 else '','argsRaw':参 if 参 is not None else ''}#工具
    return {'kind':种,**{键:值 for 键,值 in 块.items() if 键!='type'}}#其它

def 转助手块列表(内容):#多块转换
    """内容块数组 → 助手块数组。"""
    if 内容 is None or len(内容)==0:#空
        return []#空
    return [转助手块(块) for 块 in 内容]#逐块

def 是令牌增量(块):#是否可见 token 增量
    """text-delta / reasoning-delta。"""
    种=块['type'] if 'type' in 块 else None#种
    return 种 in ('text-delta','reasoning-delta')#增量

def 展示失败文案(失败):#把失败对象收成展示文案
    """优先 message，其次 code，再次 str。"""
    if 失败 is None:#无
        return ''#空
    if not isinstance(失败,dict):#非载荷
        return str(失败)#兜底
    文=失败['message'] if 'message' in 失败 else None#文案
    if 文 is not None and str(文)!='':#有
        return str(文)#文
    码=失败['code'] if 'code' in 失败 else None#码
    if 码 is not None and str(码)!='':#有
        return str(码)#码
    return str(失败)#兜底
