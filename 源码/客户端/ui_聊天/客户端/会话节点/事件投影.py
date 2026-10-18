import json

__all__=[
    '上下文形态','上下文生产者','会话召回标签','技能调用名',
    '转助手块列表','转助手块','空助手块','展示失败','是令牌增量',
]

已知形态=('instructions','catalog','snapshot','notice','relay','recall')


def 是记录(值):
    '普通对象才按字段读。数组不是记录'
    return isinstance(值,dict)


def 读字符串(记录,键):
    '非空字符串才收下'
    值=记录.get(键)
    if isinstance(值,str) and 值!='':
        return 值
    return None


def 收集(来源,成员,字段):
    '按出现顺序收集不重复的字符串'
    列表=来源.get(成员)
    if not isinstance(列表,list):
        return []
    已见=[]
    for 项 in 列表:
        记录=项 if 是记录(项) else None
        值=None if 记录 is None else 读字符串(记录,字段)
        if 值 is not None and 值 not in 已见:
            已见.append(值)
    return 已见


def 拼接(名称表):
    '有名字才拼成一行'
    if len(名称表)>0:
        return ', '.join(名称表)
    return None


def 上下文形态(来源):
    '聊天能结构化展示的 form。不认识的合并值保持不透明'
    记录=来源 if 是记录(来源) else None
    形态=None if 记录 is None else 读字符串(记录,'form')
    if 形态 is not None and 形态 in 已知形态:
        return 形态
    return None


def 上下文生产者(来源):
    '持久消息来源投影成角色和生产者标签'
    记录=来源 if 是记录(来源) else None
    种类=None if 记录 is None else 读字符串(记录,'kind')
    if 记录 is None or 种类 is None:
        return {'role':'inject','label':None}
    if 种类=='session-reference':
        return {'role':'recall','label':拼接(收集(记录,'references','label')) or 种类}
    if 种类=='agent-instructions':
        return {'role':'inject','label':拼接(收集(记录,'changes','path')) or 种类}
    if 种类=='skill-invocation':
        return {'role':'inject','label':读字符串(记录,'name') or 种类}
    return {'role':'inject','label':种类}


def 会话召回标签(来源):
    '跨会话召回引用过的标签，按首次出现排序'
    记录=来源 if 是记录(来源) else None
    if 记录 is None or 读字符串(记录,'kind')!='session-reference':
        return []
    return 收集(记录,'references','label')


def 技能调用名(来源):
    '技能注入记下的技能名。别的来源是 None'
    记录=来源 if 是记录(来源) else None
    if 记录 is None or 读字符串(记录,'kind')!='skill-invocation':
        return None
    return 读字符串(记录,'name')


def 转助手块(块):
    '一块已定稿的助手内容，按聊天要画的种类归类'
    类型=块.get('type')
    if 类型=='text':
        return {'kind':'text','text':块.get('text')}
    if 类型=='reasoning':
        return {'kind':'reasoning','text':块.get('text')}
    if 类型=='image':
        return {'kind':'image','attachment':块.get('attachment')}
    if 类型=='tool-call':
        return {
            'kind':'tool-call',
            'callId':str(块.get('id')),
            'name':块.get('name'),
            'argsRaw':块.get('arguments'),
        }
    return {'kind':'other','block':块}


def 转助手块列表(内容):
    '已定稿助手内容按原顺序归类'
    return [转助手块(块) for 块 in 内容]


def 空助手块(块类型):
    '一种流式块开始时的空块，准备接收增量'
    if 块类型=='text':
        return {'kind':'text','text':''}
    if 块类型=='reasoning':
        return {'kind':'reasoning','text':''}
    if 块类型=='tool-call':
        return {'kind':'tool-call','callId':'','name':'','argsRaw':''}
    return {'kind':'other','block':None}


def 展示失败(失败):
    '持久失败收成聊天能留的字段。AUTH 的原文可能带凭证，界面状态里不留'
    if not isinstance(失败,dict):
        return {'message':str(失败)}
    码=失败.get('code')
    码=码 if isinstance(码,str) else None
    if 码=='AUTH':
        return {'code':码,'message':''}
    消息=失败.get('message')
    if not isinstance(消息,str):
        消息=json.dumps(失败,ensure_ascii=False)
    结果={'message':消息}
    if 码 is not None:
        结果['code']=码
    return 结果


def 是令牌增量(块):
    '这条流式块有没有可见的模型输出，用来记时间'
    类型=块.get('type') if isinstance(块,dict) else None
    if 类型=='text-delta' or 类型=='reasoning-delta':
        return 块.get('text')!=''
    if 类型=='tool-call-delta':
        return 块.get('argumentsDelta')!='' or 块.get('name') is not None
    return False
