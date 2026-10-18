'轨迹自己的事件到账本视图转换。聊天列另有一份，互不调用'
import json

__all__=['上下文表单','上下文出处','转助手块列表','转助手块','空助手块','展示失败','是否令牌增量']

已知表单=('instructions','catalog','snapshot','notice','relay','recall')#结构上认得的 form

def 记录对象(值):
    '普通对象；数组与标量不是'
    if isinstance(值,dict):
        return 值
    return None

def 读字符串(记录,键):
    '非空字符串，否则 None'
    值=记录.get(键)
    if isinstance(值,str) and len(值)>0:
        return 值
    return None

def 收集(来源,成员,字段):
    '从对象列表里按字段收集不重复的非空字符串'
    列表=来源.get(成员)
    if not isinstance(列表,list):
        return []
    见过=[]
    for 项 in 列表:
        记录=记录对象(项)
        值=None if 记录 is None else 读字符串(记录,字段)
        if 值 is not None and 值 not in 见过:
            见过.append(值)
    return 见过

def 拼接名(名称列表):
    '有名字才用逗号接上'
    if len(名称列表)>0:
        return ', '.join(名称列表)
    return None

def 上下文表单(来源):
    '从耐久消息来源读轨迹认得的呈现表单；不认得则为 None'
    记录=记录对象(来源)
    表单=None if 记录 is None else 读字符串(记录,'form')
    if 表单 is not None and 表单 in 已知表单:
        return 表单
    return None

def 上下文出处(来源):
    '把耐久消息来源投影成行上的角色和生产者标签'
    记录=记录对象(来源)
    种类=None if 记录 is None else 读字符串(记录,'kind')
    if 记录 is None or 种类 is None:
        return {'role':'inject','label':None}
    if 种类=='session-reference':
        return {'role':'recall','label':拼接名(收集(记录,'references','label')) or 种类}
    if 种类=='agent-instructions':
        return {'role':'inject','label':拼接名(收集(记录,'changes','path')) or 种类}
    if 种类=='skill-invocation':
        return {'role':'inject','label':读字符串(记录,'name') or 种类}
    return {'role':'inject','label':种类}#未知生产者仍显示耐久 kind

def 转助手块(块):
    '把一块定稿助手内容分成轨迹块'
    类型=块.get('type') if isinstance(块,dict) else None
    if 类型=='text':
        return {'kind':'text','text':块.get('text') or ''}
    if 类型=='reasoning':
        return {'kind':'reasoning','text':块.get('text') or ''}
    if 类型=='image':
        return {'kind':'image','attachment':块.get('attachment')}
    if 类型=='tool-call':
        return {
            'kind':'tool-call',
            'callId':str(块.get('id') or ''),
            'name':块.get('name') or '',
            'argsRaw':块.get('arguments') or '',
        }
    return {'kind':'other','block':块}

def 转助手块列表(内容):
    '按源顺序分类定稿助手内容'
    return [转助手块(块) for 块 in 内容]

def 空助手块(块类型):
    '按流式块种类播种空块'
    if 块类型=='text':
        return {'kind':'text','text':''}
    if 块类型=='reasoning':
        return {'kind':'reasoning','text':''}
    if 块类型=='tool-call':
        return {'kind':'tool-call','callId':'','name':'','argsRaw':''}
    return {'kind':'other','block':None}

def 展示失败(失败):
    '把耐久失败收成可放进界面状态的字段。AUTH 不保留原文'
    if not isinstance(失败,dict):
        return {'message':str(失败)}
    码=失败.get('code') if isinstance(失败.get('code'),str) else None
    if 码=='AUTH':
        return {'code':码,'message':''}
    消息=失败.get('message')
    if not isinstance(消息,str):
        消息=json.dumps(失败,ensure_ascii=False)#与上游 JSON.stringify 相同，循环引用时抛出
    if 码 is None:
        return {'message':消息}
    return {'code':码,'message':消息}

def 是否令牌增量(块):
    '流式块是否带可见模型输出，用来记首 token 时间'
    类型=块.get('type') if isinstance(块,dict) else None
    if 类型 in ('text-delta','reasoning-delta'):
        return 块.get('text')!=''
    if 类型=='tool-call-delta':
        return 块.get('argumentsDelta')!='' or 块.get('name') is not None
    return False
