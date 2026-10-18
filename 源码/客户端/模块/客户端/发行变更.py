from .通告 import 取握手窗口
from ....基础设施.通用工具 import 紧凑json编码#发行身份文本
from .通告 import 可观察快照,通知订阅者#快照源与派发


__all__=['发行变更门']#仅中文公开名


def 同一发行(左,右):
    '两份发行相同：都缺席，或 version 与 commit 都相等'
    左版=None if 左 is None else 左.get('version')#左版本
    右版=None if 右 is None else 右.get('version')#右版本
    左交=None if 左 is None else 左.get('commit')#左提交
    右交=None if 右 is None else 右.get('commit')#右提交
    return 左版==右版 and 左交==右交#字段全等


def 描述发行(发行):
    '发行身份的诊断文本。缺席写 none'
    if 发行 is None:#没有发行
        return 'none'#缺席
    return 紧凑json编码(发行)#原文对象


class 发行变更门:
    '只允许页面启动时那一版宿主图。另一版等页面重新加载'
    def __init__(自身,页面):
        '从启动图的发行开始。页面是启动时的发行，可以缺席'
        自身.页面=页面#本页发行
        自身.宿主=页面#当前连上的宿主，起初与本页相同
        自身.快照=None#要通告的变化，没有则 None
        自身.监听器=set()#变化订阅
        自身.已放下=None#上次放下的宿主发行，用盒子装，因为没发布也是一种值
        def 读取():
            '当前要通告的变化'
            return 自身.快照#可能是 None
        def 订阅(监听器):
            '订阅变化'
            自身.监听器.add(监听器)#加
            def 退订():
                '去掉这个监听'
                自身.监听器.discard(监听器)#退
            return 退订#退订函数
        自身.change=可观察快照(读取,订阅)#协议名 change

    @property
    def 匹配(自身):
        '宿主是否仍是本页启动时的发行。只有这时才应用图和重建帧'
        return 同一发行(自身.宿主,自身.页面)#同版

    def 观察(自身,发行):
        '记下收到的宿主发行并更新通告。属于本页发行时返回真'
        先前=自身.宿主#换之前
        自身.宿主=发行#换成收到的
        安静=自身.匹配 or (自身.已放下 is not None and 同一发行(发行,自身.已放下['release']))#同版或已放下
        if 安静:#不再通告
            if 自身.快照 is not None:#之前有通告
                自身.发布(None)#清掉
        elif 自身.快照 is None or not 同一发行(自身.快照.get('host'),发行):#宿主发行变了
            取握手窗口().console.warn(#页面警告
                'client-modules: Host release changed from '+描述发行(先前)+' to '+描述发行(发行)+'; plugin updates pause until this page reloads',
            )#警告结束
            自身.发布({'page':自身.页面,'previous':先前,'host':发行})#通告三端
        return 自身.匹配#能否应用这张图

    def 放下(自身):
        '停止通告当前宿主发行。本页仍不应用其他发行'
        if 自身.快照 is None:#没有通告
            return#停
        自身.已放下={'release':自身.宿主}#记下放下的发行
        自身.发布(None)#清通告

    def 发布(自身,快照):
        '写快照并通知监听'
        自身.快照=快照#写
        通知订阅者(自身.监听器,'release change')#派发
