'会话和宿主目录共用的权威查询与删除。调用同步返回'
from ...模块.客户端.通告 import 取握手窗口

__all__=['创建目录源']

def 创建目录源(依赖):
    '订阅跟着框架订阅者走。删除各自返回 deleted、failed 或 pending'
    快照={'records':[],'status':'loading','deleting':[],'settled':False,'readRequest':0,'readSettled':0}
    监听列=set()
    拆除列=[]
    纪元=0
    生命周期=0
    批处理中=False
    飞行中=None
    飞行请求号=0

    def 发布(下一份):
        '换上快照并通知当前监听'
        nonlocal 快照
        快照=下一份
        for 监听 in list(监听列):
            监听()

    def 读取(请求号,当前代):
        '拉一次列表。传输失败和远端失败都变成可重试的 error'
        nonlocal 快照
        try:
            结果=依赖['list']()
        except Exception:
            if 当前代==纪元:
                发布({**快照,'status':'error'})
            return
        if 当前代!=纪元:
            return
        if 结果.get('ok'):
            发布({**快照,'records':结果['value'],'status':'ready','settled':True,'readSettled':请求号})
        else:
            发布({**快照,'status':'error'})

    def 刷新(取代=False,起始=0):
        '同一轮里后到的请求共享这一次读取。取代则另开一次'
        nonlocal 纪元,批处理中,飞行中,飞行请求号
        请求号=快照['readRequest']+1
        发布({**快照,'status':'loading','readRequest':请求号})
        if (not 取代) and 批处理中 and 飞行中 is not None and 飞行请求号>起始:
            return
        窗口=取握手窗口()
        if not 批处理中:
            批处理中=True
            def 清批():
                '这一轮提交结束'
                nonlocal 批处理中
                批处理中=False
            窗口.queueMicrotask(清批)
        当前代=纪元+1
        纪元=当前代
        待定=object()
        飞行请求号=请求号
        飞行中=待定
        def 收尾():
            '这次读取不再可加入'
            nonlocal 飞行中
            if 飞行中 is 待定:
                飞行中=None
        窗口.queueMicrotask(收尾)
        读取(请求号,当前代)

    def 作废():
        '变更或断线重连要盖过正在进行的读取'
        刷新(True)

    def 删除(标识):
        '同一条正在删则 pending。确认后强制再读一次'
        nonlocal 快照
        if 标识 in 快照['deleting']:
            return 'pending'
        开始代=生命周期
        发布({**快照,'deleting':[*快照['deleting'],标识]})
        try:
            结果=依赖['remove'](标识)
        except Exception:
            if 开始代==生命周期:
                留下=[值 for 值 in 快照['deleting'] if 值!=标识]
                发布({**快照,'deleting':留下})
            return 'failed'
        if 开始代!=生命周期:
            return 'deleted' if 结果.get('ok') else 'failed'
        留下=[值 for 值 in 快照['deleting'] if 值!=标识]
        发布({**快照,'deleting':留下})
        if 结果.get('ok'):
            刷新(True)
        return 'deleted' if 结果.get('ok') else 'failed'

    def 订阅(监听):
        '第一个订阅者才去订远端，并立刻作废读取'
        nonlocal 拆除列,纪元,生命周期,快照
        监听列.add(监听)
        if len(监听列)==1:
            生命周期=生命周期+1
            拆除列=[依赖['subscribeChanged'](作废),依赖['subscribeReset'](作废)]
            作废()
        def 退订():
            '最后一个离开就拆订阅，并清掉进行中的删除'
            nonlocal 拆除列,纪元,生命周期,快照
            监听列.discard(监听)
            if len(监听列)!=0:
                return
            for 拆除 in 拆除列:
                拆除()
            拆除列=[]
            纪元=纪元+1
            生命周期=生命周期+1
            快照={**快照,'deleting':[]}
        return 退订

    def 重试(起始=0):
        '失败或写回之后再读。起始是调用方见过的请求序号'
        刷新(False,起始)

    def 取快照():
        '当前目录快照'
        return 快照

    return {
        'hooks':{
            'catalog':{
                'getSnapshot':取快照,
                'subscribe':订阅,
            },
        },
        'onDelete':删除,
        'onRetry':重试,
    }
