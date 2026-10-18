from ...异常 import 聊天错误

__all__=['最大工具调用树深度','工具调用树']

最大工具调用树深度=256


def 引用相同(左,右):
    '长度和每一项身份都一样'
    if len(左)!=len(右):
        return False
    下标=0
    for 项 in 左:
        if 项 is not 右[下标]:
            return False
        下标+=1
    return True


def 参数自对象(值):
    'PTC 参数视图。工具.值 还没有 PartialArguments.fromObject'
    raise 聊天错误('缺少 工具.值 的 PartialArguments.fromObject')


class 工具调用树:
    'PTC 派发配对，并把私有父索引投影成快照里的递归工具调用'
    def __init__(自身):
        '空树'
        自身.子调用={}
        自身.深度={}
        自身.投影={}
        自身.修订=0
        自身.节点缓存=None
        自身.运行缓存=None

    def reset(自身):
        '重放新窗口前忘掉派生来的子调用'
        自身.子调用={}
        自身.深度={}
        自身.投影={}
        自身.修订+=1

    def apply(自身,事件):
        '吃掉 PTC 派发事件。其他事件返回假'
        if not isinstance(事件,dict):
            return False
        if 事件.get('type')=='tool/ptc-dispatch-start':
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
            运行={
                'phase':'start',
                'callId':数据.get('subCallId'),
                'parentCallId':数据.get('parentCallId'),
                'name':数据.get('name'),
                'argsRaw':'',
                'args':参数自对象(数据.get('arguments')),
                'turn':0,
                'step':0,
                'time':事件.get('time'),
                'subCalls':[],
            }
            兄弟=list(自身.子调用.get(数据.get('parentCallId'),[]))
            if not 自身.接受边(数据.get('parentCallId'),数据.get('subCallId')):
                return True
            兄弟.append(运行)
            自身.子调用[数据.get('parentCallId')]=兄弟
            自身.修订+=1
            return True
        if 事件.get('type')!='tool/ptc-dispatch':
            return False
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        兄弟=list(自身.子调用.get(数据.get('parentCallId'),[]))
        处=-1
        下标=0
        for 子 in 兄弟:
            if isinstance(子,dict) and 子.get('callId')==数据.get('subCallId'):
                处=下标
                break
            下标+=1
        if 处<0 and not 自身.接受边(数据.get('parentCallId'),数据.get('subCallId')):
            return True
        已开始=None if 处<0 else 兄弟[处]
        结算={
            'kind':'tool-result',
            'seq':事件.get('seq'),
            'time':事件.get('time'),
            'callId':数据.get('subCallId'),
            'parentCallId':数据.get('parentCallId'),
            'name':数据.get('name'),
            'args':已开始.get('args') if isinstance(已开始,dict) and 'kind' not in 已开始 else 参数自对象(数据.get('arguments')),
            'call':{'name':数据.get('name'),'argsRaw':''},
            'callTime':已开始.get('time') if isinstance(已开始,dict) else None,
            'content':数据.get('content'),
            'isError':数据.get('isError'),
            'subCalls':[],
        }
        if 处<0:
            兄弟.append(结算)
        else:
            兄弟[处]=结算
        自身.子调用[数据.get('parentCallId')]=兄弟
        自身.修订+=1
        return True

    def projectNodes(自身,节点表):
        '给定稿根挂上递归子调用。没变就留原列表'
        if 自身.节点缓存 is not None and 自身.节点缓存['source'] is 节点表 and 自身.节点缓存['revision']==自身.修订:
            return 自身.节点缓存['value']
        投影=[]
        for 节点 in 节点表:
            if isinstance(节点,dict) and 节点.get('kind')=='tool-result':
                投影.append(自身.投影块(节点))
            else:
                投影.append(节点)
        值=节点表 if 引用相同(节点表,投影) else 投影
        自身.节点缓存={'source':节点表,'revision':自身.修订,'value':值}
        return 值

    def projectRunningCalls(自身,调用表):
        '给还在跑的根挂上递归子调用'
        if 自身.运行缓存 is not None and 自身.运行缓存['source'] is 调用表 and 自身.运行缓存['revision']==自身.修订:
            return 自身.运行缓存['value']
        投影=[自身.投影块(调用) for 调用 in 调用表]
        值=调用表 if 引用相同(调用表,投影) else 投影
        自身.运行缓存={'source':调用表,'revision':自身.修订,'value':值}
        return 值

    def 投影块(自身,块):
        '递归挂子调用。缓存按块身份'
        if not isinstance(块,dict):
            return 块
        if 'kind' not in 块 and 块.get('phase')=='preparing':
            return 块
        子=自身.子调用.get(块.get('callId'),块.get('subCalls') or [])
        投影子=[自身.投影块(子项) for 子项 in 子]
        子值=子 if 引用相同(子,投影子) else 投影子
        缓存=自身.投影.get(块.get('callId'))
        if 缓存 is not None and 缓存['source'] is 块 and 引用相同(缓存['children'],子值):
            return 缓存['value']
        if 块.get('subCalls') is 子值:
            值=块
        else:
            值=dict(块)
            值['subCalls']=子值
        自身.投影[块.get('callId')]={'source':块,'children':子值,'value':值}
        return 值

    def 接受边(自身,父标识,子标识):
        '成环或超过深度上限的边吃掉，但不藏起会话其余部分'
        if 自身.会成环(父标识,子标识):
            return False
        待定=[{'callId':子标识,'depth':自身.深度.get(父标识,1)+1}]
        更新={}
        for 候选 in 待定:
            已知=更新.get(候选['callId'],自身.深度.get(候选['callId'],1))
            if 候选['depth']<=已知:
                continue
            if 候选['depth']>最大工具调用树深度:
                return False
            更新[候选['callId']]=候选['depth']
            for 子 in 自身.子调用.get(候选['callId'],[]):
                if isinstance(子,dict):
                    待定.append({'callId':子.get('callId'),'depth':候选['depth']+1})
        for 标识,深度 in 更新.items():
            自身.深度[标识]=深度
        return True

    def 会成环(自身,父标识,子标识):
        '从子标识往下能不能走回父标识'
        if 父标识==子标识:
            return True
        待定=[子标识]
        已访=set(待定)
        for 标识 in list(待定):
            for 子 in 自身.子调用.get(标识,[]):
                if not isinstance(子,dict):
                    continue
                if 子.get('callId')==父标识:
                    return True
                if 子.get('callId') in 已访:
                    continue
                已访.add(子.get('callId'))
                待定.append(子.get('callId'))
        return False
