'从已记录的 propose_action 调用恢复提案，从插件记录恢复决定'
import json
from ...模型后端.llm import 调用标识
from ...内核.会话 import 插件记录于
from ...工具.值 import 是否json值
from ...基础设施.通用工具 import 最大安全整数,是否非负安全整数,是否有限json数字,是否有限数,是否整值数

__all__=['提议动作','操作卡片投影','日志偏移']

提议动作='propose_action'

def 日志偏移(值):
    '接纳非负安全整数为会话日志偏移。内核.会话 未导出 SessionLogOffset'
    if isinstance(值,bool) or not 是否非负安全整数(值) or not 是否有限json数字(值):
        raise TypeError('SessionLogOffset must be a non-negative safe integer, got '+str(值))
    return int(值)

class 校验结果:
    'safeParse 的结果。成功有 data，失败有 error.issues'
    def __init__(自身,成功,数据=None,问题=None):
        '记下是否通过'
        自身.success=成功
        自身.data=数据
        自身.error=None if 成功 else type('问题集',(),{'issues':问题 or []})()

def 问题(路径,消息):
    '一条字段问题'
    return {'path':路径,'message':消息}

def 是记录(值):
    '普通对象。数组不是'
    return isinstance(值,dict)

def 是正文字(值):
    '去掉空白后仍有字符的字符串，返回去掉空白的文本'
    if not isinstance(值,str):
        return None
    文本=值.strip()
    if len(文本)==0:
        return None
    return 文本

def 是非空串(值):
    '长度至少为一的字符串'
    return isinstance(值,str) and len(值)>=1

def 是非负整数(值):
    '非负整数，拒绝布尔和负零'
    return (not isinstance(值,bool)) and 是否整值数(值) and 是否有限json数字(值) and 值>=0

def 是整数(值):
    '任意整数，拒绝布尔和负零'
    if isinstance(值,bool) or not 是否整值数(值) or not 是否有限json数字(值):
        return False
    return True

def 是有限数字(值):
    '有限数字，拒绝布尔'
    return 是否有限数(值) and 是否有限json数字(值)

def 校验字段(值):
    '种类自定义的 JSON 对象'
    if not 是记录(值):
        return 校验结果(False,问题=[问题([],'expected object')])
    for 键,项 in 值.items():
        if not isinstance(键,str) or not 是否json值(项):
            return 校验结果(False,问题=[问题([键],'expected json')])
    return 校验结果(True,dict(值))

def 校验参数(值):
    'propose_action 的参数。空白标题或说明不成卡片'
    if not 是记录(值):
        return 校验结果(False,问题=[问题([],'expected object')])
    收集=[]
    if not 是非空串(值.get('action')):
        收集.append(问题(['action'],'too small'))
    标题=是正文字(值.get('title'))
    if 标题 is None:
        收集.append(问题(['title'],'too small'))
    说明=是正文字(值.get('brief'))
    if 说明 is None:
        收集.append(问题(['brief'],'too small'))
    细节=校验字段(值.get('details'))
    if not 细节.success:
        收集.extend(细节.error.issues)
    if 收集:
        return 校验结果(False,问题=收集)
    return 校验结果(True,{
        'action':值['action'],
        'title':标题,
        'brief':说明,
        'details':细节.data,
    })

def 校验提案(值,要调用标识=True):
    '一张提案。调用记录可以先不带 callId'
    if not 是记录(值):
        return 校验结果(False,问题=[问题([],'expected object')])
    允许={'turn','action','title','brief','details'}
    if 要调用标识:
        允许={'callId','turn','action','title','brief','details'}
    if any(键 not in 允许 for 键 in 值):
        return 校验结果(False,问题=[问题([],'unrecognized key')])
    收集=[]
    调用=None
    if 要调用标识:
        if not 是非空串(值.get('callId')):
            收集.append(问题(['callId'],'too small'))
        else:
            调用=调用标识(值['callId'])
    if not 是非负整数(值.get('turn')):
        收集.append(问题(['turn'],'expected nonnegative int'))
    if not 是非空串(值.get('action')) or not 是非空串(值.get('title')) or not 是非空串(值.get('brief')):
        收集.append(问题([],'expected non-empty string'))
    细节=校验字段(值.get('details'))
    if not 细节.success:
        收集.extend(细节.error.issues)
    if 收集:
        return 校验结果(False,问题=收集)
    数据={'turn':int(值['turn']),'action':值['action'],'title':值['title'],'brief':值['brief'],'details':细节.data}
    if 要调用标识:
        数据['callId']=调用
    return 校验结果(True,数据)

def 校验决定(值):
    '一张已记录的决定'
    if not 是记录(值):
        return 校验结果(False,问题=[问题([],'expected object')])
    允许={'callId','action','phase','data'}
    if any(键 not in 允许 for 键 in 值):
        return 校验结果(False,问题=[问题([],'unrecognized key')])
    if not 是非空串(值.get('callId')) or not 是非空串(值.get('action')) or not 是非空串(值.get('phase')):
        return 校验结果(False,问题=[问题([],'expected non-empty string')])
    数据={'callId':调用标识(值['callId']),'action':值['action'],'phase':值['phase']}
    if 'data' in 值 and 值['data'] is not None:
        细节=校验字段(值['data'])
        if not 细节.success:
            return 细节
        数据['data']=细节.data
    return 校验结果(True,数据)

def 校验视图(值):
    '客户端看到的提案表和决定表'
    if not 是记录(值) or not 是记录(值.get('proposals')) or not 是记录(值.get('decisions')):
        return 校验结果(False,问题=[问题([],'expected view')])
    提案={}
    for 键,项 in 值['proposals'].items():
        解析=校验提案(项,True)
        if not 解析.success:
            return 解析
        提案[键]=解析.data
    决定={}
    for 键,项 in 值['decisions'].items():
        解析=校验决定(项)
        if not 解析.success:
            return 解析
        决定[键]=解析.data
    return 校验结果(True,{'proposals':提案,'decisions':决定})

def 校验状态(值):
    '折叠状态。view 同时是客户端线路值'
    if not 是记录(值):
        raise ValueError('action card state must be an object')
    if not 是非负整数(值.get('inheritedEventCount')) or 值['inheritedEventCount']>最大安全整数:
        raise ValueError('inheritedEventCount must be a non-negative safe integer')
    视图=校验视图(值.get('view'))
    if not 视图.success:
        raise ValueError('invalid action card view')
    if not 是记录(值.get('calls')) or not 是记录(值.get('pendingStatus')):
        raise ValueError('invalid action card maps')
    调用表={}
    for 键,项 in 值['calls'].items():
        解析=校验提案(项,False)
        if not 解析.success:
            raise ValueError('invalid pending call')
        调用表[键]=解析.data
    待报={}
    for 键,项 in 值['pendingStatus'].items():
        if not 是有限数字(项):
            raise ValueError('pending status seq must be a number')
        待报[键]=项
    接纳轮次=值.get('admittedTurn')
    if 接纳轮次 is not None and not 是整数(接纳轮次):
        raise ValueError('admittedTurn must be an int or null')
    if not 是非负整数(值.get('queued')):
        raise ValueError('queued must be a nonnegative int')
    return {
        'inheritedEventCount':日志偏移(值['inheritedEventCount']),
        'view':视图.data,
        'calls':调用表,
        'admittedTurn':None if 接纳轮次 is None else int(接纳轮次),
        'pendingStatus':待报,
        'queued':int(值['queued']),
    }

def 解析视图(值):
    '视图模式被注册表当成函数调用，失败则抛出'
    结果=校验视图(值)
    if not 结果.success:
        raise ValueError('invalid action card view')
    return 结果.data

def 取出视图(状态):
    '客户端线路值就是折叠状态里的 view'
    return 状态['view']

def 初态(_头=None,继承事件数=0):
    '空日志。注册表目前只传入头时，继承条数为 0'
    if 继承事件数 is None:
        继承事件数=0
    return {
        'inheritedEventCount':日志偏移(继承事件数),
        'view':{'proposals':{},'decisions':{}},
        'calls':{},
        'admittedTurn':None,
        'pendingStatus':{},
        'queued':0,
    }

def 应用(状态,事件):
    '成功的 propose_action 至多每轮收一张；更新的卡片替换尚未开始的旧卡片'
    if 事件['seq']<状态['inheritedEventCount']:
        return 状态
    类型=事件['type']
    if 类型=='turn/start':
        if len(状态['calls'])==0:
            return 状态
        下一=dict(状态)
        下一['calls']={}
        return 下一
    if 类型=='agent/inbox/spliced':
        if 事件['data']['target']!='next-turn':
            return 状态
        移除=事件['data']['removedCount'] if 'removedCount' in 事件['data'] and 事件['data']['removedCount'] is not None else 0
        下一=dict(状态)
        下一['queued']=max(0,状态['queued']-移除+len(事件['data']['inserted']))
        return 下一
    if 类型=='user/message':
        if 事件['data']['source']['kind']!='action-cards':
            return 状态
        通过=事件['data']['source']['through']
        下一=dict(状态)
        下一['pendingStatus']={键:序号 for 键,序号 in 状态['pendingStatus'].items() if 序号>通过}
        return 下一
    if 类型=='tool/call':
        if 事件['data']['name']!=提议动作:
            return 状态
        try:
            原始=json.loads(事件['data']['arguments'])
        except (TypeError,ValueError):
            return 状态
        解析=校验参数(原始)
        if not 解析.success:
            return 状态
        调用=dict(状态['calls'])
        调用[事件['data']['callId']]={'turn':事件['data']['turn'],**解析.data}
        下一=dict(状态)
        下一['calls']=调用
        return 下一
    if 类型=='tool/result':
        调用标识值=事件['data']['message']['toolCallId']
        if 调用标识值 not in 状态['calls']:
            return 状态
        调用=状态['calls'][调用标识值]
        剩余={键:项 for 键,项 in 状态['calls'].items() if 键!=调用标识值}
        if 事件['data']['message'].get('isError') is True or 状态['admittedTurn']==调用['turn']:
            下一=dict(状态)
            下一['calls']=剩余
            return 下一
        决定=dict(状态['view']['decisions'])
        for 较早 in 状态['view']['proposals'].values():
            if 较早['callId'] not in 决定:
                决定[较早['callId']]={'callId':较早['callId'],'action':较早['action'],'phase':'replaced'}
        提案=dict(状态['view']['proposals'])
        提案[调用标识值]={'callId':调用标识值,**调用}
        下一=dict(状态)
        下一['calls']=剩余
        下一['admittedTurn']=调用['turn']
        下一['view']={'proposals':提案,'decisions':决定}
        return 下一
    记录=插件记录于(事件)
    if 记录 is None or 记录['type']!='plugin:action-cards/decision':
        return 状态
    决定=校验决定(记录['data'])
    if not 决定.success:
        return 状态
    决定表=dict(状态['view']['decisions'])
    决定表[决定.data['callId']]=决定.data
    待报=dict(状态['pendingStatus'])
    待报[决定.data['callId']]=事件['seq']
    下一=dict(状态)
    下一['view']={'proposals':状态['view']['proposals'],'decisions':决定表}
    下一['pendingStatus']=待报
    return 下一

操作卡片投影={
    'key':'actionCards',
    'stateVersion':2,
    'stateSchema':校验状态,
    'init':初态,
    'apply':应用,
    'wire':{'summary':False,'viewSchema':解析视图,'view':取出视图},
}
