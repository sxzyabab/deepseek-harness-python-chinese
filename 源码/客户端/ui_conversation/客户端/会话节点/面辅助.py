"""会话节点用的运行时面谓词与助手块转换（本地最小实现）。

对齐上游 `@deepseek-ai/dsh-client-runtime/client` 中本包实际用到的面。
不额外依赖；按事件字段鸭式读取。
"""

__all__=[#公开
    '取字段','是追加面事件','是替换面事件','上下文出处','上下文形态',
    '空助手块','转助手块','转助手块们','是令牌增量','展示失败文案',
]#公开结束

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 是追加面事件(事件):#是否追加面
    """surface==append 或缺省视为追加。"""
    面=取字段(事件,'surface')#面
    if 面 is None:#缺省
        数据=取字段(事件,'data')#载荷
        面=取字段(数据,'surface')#嵌套
    return 面 in (None,'append','append-surface')#追加

def 是替换面事件(事件):#是否替换面
    """surface==replace / replacement。"""
    面=取字段(事件,'surface')#面
    if 面 is None:#缺省
        数据=取字段(事件,'data')#载荷
        面=取字段(数据,'surface')#嵌套
    return 面 in ('replace','replacement','replace-surface')#替换

def 上下文出处(来源):#角色与生产者名
    """从持久化来源投影 provenance。"""
    种=取字段(来源,'kind')#种类
    if 种=='user':#用户
        return {'role':'user','producer':'user'}#用户
    if 种=='plugin':#插件
        return {'role':'context','producer':取字段(来源,'plugin') or 'plugin'}#插件名
    return {'role':'context','producer':str(种 or 'unknown')}#其它

def 上下文形态(来源):#生产者声明的信息形态
    """有 form 则原样，否则 generic。"""
    形=取字段(来源,'form')#形态
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
    if isinstance(块,dict):#已是映射
        if 'kind' in 块:#已有
            return 块#原样
        种=块.get('type')#type → kind
        if 种=='text':#文本
            return {'kind':'text','text':块.get('text','')}#文本
        if 种=='reasoning':#推理
            return {'kind':'reasoning','text':块.get('text','')}#推理
        if 种=='tool-call':#工具
            return {'kind':'tool-call','callId':str(块.get('id') or 块.get('callId') or ''),'name':块.get('name',''),'argsRaw':块.get('arguments') or 块.get('argsRaw') or ''}#工具
        return {'kind':种,**{键:值 for 键,值 in 块.items() if 键!='type'}}#其它
    return 块#对象原样

def 转助手块们(内容):#多块转换
    """内容块数组 → 助手块数组。"""
    if not 内容:#空
        return []#空
    return [转助手块(块) for 块 in 内容]#逐块

def 是令牌增量(块):#是否可见 token 增量
    """text-delta / reasoning-delta。"""
    种=取字段(块,'type')#种
    return 种 in ('text-delta','reasoning-delta')#增量

def 展示失败文案(失败):#把失败对象收成展示文案
    """优先 message，其次 code，再次 str。"""
    if 失败 is None:#无
        return ''#空
    文=取字段(失败,'message')#文案
    if 文:#有
        return str(文)#文
    码=取字段(失败,'code')#码
    if 码:#有
        return str(码)#码
    return str(失败)#兜底
