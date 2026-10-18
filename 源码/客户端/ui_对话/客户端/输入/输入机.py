'每个会话的提交平面。事件进去，效果出来'
import re
from ....模块.客户端.通告 import 取握手窗口

__all__=['提交机']

def 令牌之后(草稿,令牌):
    '从提交时的草稿里拿掉已认领的命令令牌'
    文=草稿.lstrip()
    if 文.startswith(令牌):
        return 文[len(令牌):]
    基=令牌.rstrip()
    if 文.startswith(基):
        余=文[len(基):]
        if 余[:1].isspace():
            return 余[1:]
        return 余
    return ''

class 提交机:
    '阶段、认领和在途尝试'
    def __init__(自身):
        '从普通阶段开始'
        自身.阶段='plain'
        自身.认领=None
        自身.序号=0
        自身.在途=None
        自身.脱离={}

    def 状态(自身):
        '只读的提交平面'
        出={'phase':自身.阶段}
        if 自身.认领 is not None:
            认领={'name':自身.认领['name'],'token':自身.认领['token']}
            if 自身.认领.get('hint') is not None:
                认领['hint']=自身.认领['hint']
            if 自身.认领.get('attachments') is True:
                认领['attachments']=True
            出['claim']=认领
        return 出

    def 派发(自身,事件):
        '喂进一条事件，按顺序返回效果'
        类型=事件['type']
        if 类型=='draft-changed':
            return 自身.跟随命令(事件.get('command'))
        if 类型=='claim':
            return 自身.跟随命令(事件.get('claim'))
        if 类型=='enter':
            return 自身.回车(事件['mode'],事件['draft'],事件.get('submission'))
        if 类型=='adjudicated':
            return 自身.已裁决(事件['attempt'],事件.get('outcome'))
        if 类型=='adjudication-failed':
            return 自身.裁决失败(事件['attempt'],事件['message'])
        if 类型=='submit-settled':
            return 自身.提交落定(事件)
        if 类型=='sink-settled':
            return 自身.汇落定(事件)
        if 类型=='send-committed':
            return 自身.发送已提交()
        if 类型=='release':
            return 自身.释放()
        raise Exception('unreachable input event: '+str(事件))

    def 跟随命令(自身,命令):
        '忙碌阶段不跟。没有命令就是普通，有命令就是已认领'
        if 自身.阶段!='plain' and 自身.阶段!='claimed':
            return []
        自身.认领=命令
        自身.阶段='plain' if 命令 is None else 'claimed'
        return []

    def 铸造尝试(自身,方式,草稿,提交=None):
        '造一次尝试和它的中止控制器'
        控制器=取握手窗口().AbortController()
        自身.序号+=1
        尝试={'seq':自身.序号,'signal':控制器.signal,'draftSnapshot':草稿,'mode':方式}
        if 提交 is not None:
            尝试['submission']=提交
        return {'attempt':尝试,'controller':控制器}

    def 开始尝试(自身,方式,草稿,提交=None):
        '冻结的命令或裁决尝试'
        飞行=自身.铸造尝试(方式,草稿,提交)
        自身.在途=飞行
        return 飞行['attempt']

    def 开始脱离(自身,方式,草稿,提交=None):
        '普通发送离开编辑器，阶段回到普通'
        飞行=自身.铸造尝试(方式,草稿,提交)
        自身.脱离[飞行['attempt']['seq']]=飞行['controller']
        自身.认领=None
        自身.阶段='plain'
        return 飞行['attempt']

    def 脱离效果(自身,尝试):
        '默认汇和提交草稿'
        return [
            {'type':'default-sink','attempt':尝试,'draft':尝试['draftSnapshot'],'mode':尝试['mode']},
            {'type':'commit-draft','retainSuffixOf':尝试['draftSnapshot']},
        ]

    def 回车(自身,方式,草稿,提交=None):
        '已认领走提交，斜杠行走裁决，其余脱离发送'
        if 自身.阶段 in ('adjudicating','submitting'):
            return []
        if 自身.阶段=='claimed' and 自身.认领 is not None:
            尝试=自身.开始尝试(方式,草稿,提交)
            自身.阶段='submitting'
            return [{'type':'begin-submit','attempt':尝试,'claim':自身.认领,'args':令牌之后(草稿,自身.认领['token'])}]
        修剪=草稿.strip()
        if 修剪=='':
            return []
        if 修剪.startswith('/'):
            尝试=自身.开始尝试(方式,草稿,提交)
            自身.阶段='adjudicating'
            return [{'type':'adjudicate','attempt':尝试,'draft':草稿}]
        return 自身.脱离效果(自身.开始脱离(方式,草稿,提交))

    def 已裁决(自身,尝试,结局):
        '认领就进入提交。未处理则按普通发送脱离'
        飞行=自身.在途
        if 自身.阶段!='adjudicating' or 飞行 is None or 飞行['attempt']['seq']!=尝试['seq']:
            return []
        if 结局 is not None and 结局!='handled' and 'claim' in 结局:
            自身.认领=结局['claim']
            自身.阶段='submitting'
            return [{'type':'begin-submit','attempt':尝试,'claim':结局['claim'],'args':令牌之后(尝试['draftSnapshot'],结局['claim']['token'])}]
        自身.在途=None
        自身.阶段='plain'
        if 结局 is not None:
            return []
        自身.脱离[尝试['seq']]=飞行['controller']
        return 自身.脱离效果(尝试)

    def 裁决失败(自身,尝试,消息):
        '回到普通并给出错误通知'
        if 自身.阶段!='adjudicating' or 自身.在途 is None or 自身.在途['attempt']['seq']!=尝试['seq']:
            return []
        自身.在途=None
        自身.阶段='plain'
        return [{'type':'notice','level':'error','text':消息}]

    def 提交落定(自身,事件):
        '成功就清空认领。失败则重新跟随前导命令'
        飞行=自身.在途
        if 自身.阶段!='submitting' or 飞行 is None or 飞行['attempt']['seq']!=事件['attempt']['seq']:
            return []
        自身.在途=None
        if 事件.get('ok'):
            自身.阶段='plain'
            自身.认领=None
            效果=[{'type':'commit-draft','retainSuffixOf':飞行['attempt']['draftSnapshot']}]
            结局=事件.get('outcome')
            if isinstance(结局,dict) and 结局.get('text') is not None:
                效果.append({'type':'notice','level':'error' if 结局.get('kind')=='error' else 'info','text':结局['text']})
            return 效果
        文=事件.get('message')
        if 文 is None and isinstance(事件.get('outcome'),dict):
            文=事件['outcome'].get('text')
        自身.认领=事件.get('command')
        自身.阶段='plain' if 自身.认领 is None else 'claimed'
        if 文 is None:
            return []
        return [{'type':'notice','level':'error','text':文}]

    def 汇落定(自身,事件):
        '一次普通发送独立落定'
        if 事件['attempt']['seq'] not in 自身.脱离:
            return []
        del 自身.脱离[事件['attempt']['seq']]
        文=事件.get('message')
        if 文 is None and isinstance(事件.get('outcome'),dict):
            文=事件['outcome'].get('text')
        if 文 is None:
            return []
        级别='info' if 事件.get('ok') and (not isinstance(事件.get('outcome'),dict) or 事件['outcome'].get('kind')!='error') else 'error'
        return [{'type':'notice','level':级别,'text':文}]

    def 发送已提交(自身):
        '只接受附件的发送没有要留下的后缀'
        if 自身.阶段!='plain':
            return []
        自身.认领=None
        return [{'type':'commit-draft','retainSuffixOf':None}]

    def 释放(自身):
        '中止在途和已脱离的尝试'
        if 自身.在途 is not None:
            自身.在途['controller'].abort()
            自身.在途=None
        for 控制器 in 自身.脱离.values():
            控制器.abort()
        自身.脱离.clear()
        自身.阶段='plain'
        自身.认领=None
        return []
