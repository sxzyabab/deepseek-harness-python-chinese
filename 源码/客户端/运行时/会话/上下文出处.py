"""上下文来源投影：一条已记录的非用户 `user/message` 的角色与面向人的生产者名。

对齐上游 `runtime/src/client/sessions/context-provenance.ts`。公开面仅中文名。
只从其持久化 `source` 读取。客户端不维护已知插件 id 表。
"""

__all__=['已知形态表','上下文出处','上下文形态']#仅中文公开名

已知形态表=('instructions','catalog','snapshot','notice','relay','recall')#本 UI 版本知道的形态

def 收窄记录(值):#未知值 → 记录或空
    """把未知值收窄成可读记录形态；其它一律 None。"""
    if isinstance(值,dict):#映射即记录
        return 值#当作记录
    return None#否则空

def 读字符串(记录,键):#读非空字符串字段
    """读记录里一个非空字符串字段，否则 None。"""
    值=记录.get(键)#取出字段
    if isinstance(值,str) and 值!='':#非空字符串才要
        return 值#要
    return None#否则空

def 收集(源,成员,字段):#收集字段值
    """源里某个数组成员的 `field` 去重非空值，按首次出现顺序。"""
    列表=源.get(成员)#数组成员
    if not isinstance(列表,list):#不是数组则空
        return []#空
    已见=[]#已见值
    for 项 in 列表:#逐项
        记录=收窄记录(项)#收窄成记录
        值=None if 记录 is None else 读字符串(记录,字段)#读字段
        if 值 is not None and 值 not in 已见:#去重追加
            已见.append(值)#追加
    return 已见#首次出现顺序

def 拼接(名字们):#名字列表 → 标签
    """把收集到的名字列表渲成一个标签；空列表则为 None。"""
    if len(名字们)>0:#有名字
        return ', '.join(名字们)#逗号拼接
    return None#空

def 上下文出处(源):#投影出处
    """把一条持久化消息 source 投影成 transcript 角色与生产者名。

    @param 源 - 已记录的 `user/message` source，原文。
    @returns 这段上下文要展示的角色与生产者名（role/label）。
    """
    记录=收窄记录(源)#收窄成记录
    种类=None if 记录 is None else 读字符串(记录,'kind')#kind 字段
    if 记录 is None or 种类 is None:#无 kind 则注入且无名
        return {'role':'inject','label':None}#注入无名
    if 种类=='session-reference':#会话引用
        return {'role':'recall','label':拼接(收集(记录,'references','label')) or 种类}#召回
    if 种类=='agent-instructions':#智能体指令
        return {'role':'inject','label':拼接(收集(记录,'changes','path')) or 种类}#注入路径
    if 种类=='plugin':#插件
        return {'role':'inject','label':读字符串(记录,'plugin') or 种类}#注入插件 id
    if 种类=='skill-invocation':#技能调用
        return {'role':'inject','label':读字符串(记录,'name') or 种类}#注入技能名
    return {'role':'inject','label':种类}#未知 kind：注入，标签就是 kind

def 上下文形态(源):#读上下文形态
    """从一条持久化消息 source 读出生产者声明的形态。

    @param 源 - 已记录的 `user/message` source，原文。
    @returns 本 UI 版本会展示该形态时返回它，否则 None（不透明）。
    """
    记录=收窄记录(源)#收窄成记录
    形态=None if 记录 is None else 读字符串(记录,'form')#form 字段
    if 形态 is not None and 形态 in 已知形态表:#是已知形态
        return 形态#收窄
    return None#不透明
