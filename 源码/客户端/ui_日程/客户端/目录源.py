'日程目录的可观察快照：读取、删除、刷新'
from ..异常 import 页面失败文案

__all__=['创建目录源','空目录快照']

空目录快照={'records':[],'status':'loading','deleting':[],'settled':False,'readRequest':0,'readSettled':0}

class 目录钩子:
    '带 getSnapshot 和 subscribe 方法的目录源。绑定器不认字典上的同名键'
    def __init__(自身,取,订):
        '记下读和订'
        自身._取=取
        自身._订=订

    def getSnapshot(自身):
        '当前目录快照'
        return 自身._取()

    def subscribe(自身,回调):
        '第一个订阅者才开始读'
        return 自身._订(回调)

def 创建目录源(依赖):
    'list / remove / 两路失效订阅。变更时重新拉权威列表'
    格子={'状态':dict(空目录快照)}
    监听=set()
    拆除=[]
    世代=[0]
    飞行=[None]
    飞行请求=[0]
    批=[False]

    def 发布(下一):
        '换快照并通知'
        格子['状态']=下一
        for 回调 in list(监听):
            try:
                回调()
            except Exception as 错误:
                print('目录订阅者失败:',页面失败文案(错误))

    def 应用读取(请求号,当前世代,结果):
        '成功写入记录；失败只改状态'
        if 当前世代!=世代[0]:
            return
        状态=格子['状态']
        if isinstance(结果,dict) and 'ok' in 结果 and 结果['ok'] is True and 'value' in 结果 and isinstance(结果['value'],list):
            发布({**状态,'records':结果['value'],'status':'ready','settled':True,'readSettled':请求号})
            return
        if isinstance(结果,list):
            发布({**状态,'records':结果,'status':'ready','settled':True,'readSettled':请求号})
            return
        发布({**状态,'status':'error'})

    def 读(请求号,当前世代):
        '调用 list，同步值或 thenable 都收'
        try:
            结果=依赖['list']()
        except Exception:
            if 当前世代==世代[0]:
                发布({**格子['状态'],'status':'error'})
            return
        def 成功(值):
            '读回'
            应用读取(请求号,当前世代,值)
        def 失败(_错误):
            '传输失败'
            应用读取(请求号,当前世代,{'ok':False})
        if hasattr(结果,'then') and callable(结果.then):
            结果.then(成功,失败)
            return
        成功(结果)

    def 刷新(取代=False,自从=0):
        '同一拍里的请求共用一次读取'
        状态=格子['状态']
        请求号=状态['readRequest']+1
        发布({**状态,'status':'loading','readRequest':请求号})
        if 取代 is False and 批[0] is True and 飞行[0] is not None and 飞行请求[0]>自从:
            return 飞行[0]
        批[0]=True
        当前=世代[0]+1
        世代[0]=当前
        读(请求号,当前)
        飞行请求[0]=请求号
        飞行[0]=请求号
        return 请求号

    def 失效():
        '变更或断线重读，不并进旧请求'
        刷新(True)

    def 订阅(回调):
        '订阅目录；退订到零时拆掉远端监听'
        监听.add(回调)
        if len(监听)==1:
            改=依赖['subscribeChanged'](失效)
            重=依赖['subscribeReset'](失效)
            拆除[:] = [项 for 项 in (改,重) if callable(项)]
            失效()
        def 退订():
            '最后一个订阅者离开后停止读取'
            监听.discard(回调)
            if len(监听)!=0:
                return
            for 拆 in 拆除:
                拆()
            拆除.clear()
            世代[0]+=1
            发布({**格子['状态'],'deleting':[]})
        return 退订

    def 删除(标识):
        '删一条；已在删则 pending'
        状态=格子['状态']
        正在=状态['deleting']
        if 标识 in 正在:
            return 'pending'
        发布({**状态,'deleting':[*正在,标识]})
        try:
            结果=依赖['remove'](标识)
        except Exception:
            发布({**格子['状态'],'deleting':[项 for 项 in 格子['状态']['deleting'] if 项!=标识]})
            return 'failed'
        def 收尾(值):
            '确认后刷新列表'
            发布({**格子['状态'],'deleting':[项 for 项 in 格子['状态']['deleting'] if 项!=标识]})
            成功=isinstance(值,dict) and 'ok' in 值 and 值['ok'] is True
            if 成功:
                刷新(True)
            return 'deleted' if 成功 else 'failed'
        if hasattr(结果,'then') and callable(结果.then):
            结果.then(收尾,lambda _错误:收尾({'ok':False}))
            return 'pending'
        return 收尾(结果)

    def 重试(自从=0):
        '失败或创建卡要求的新读取'
        return 刷新(False,自从)

    钩子=目录钩子(lambda:格子['状态'],订阅)
    return {'hooks':{'catalog':钩子},'onDelete':删除,'onRetry':重试}
