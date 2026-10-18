from ....存储 import 创建快照存储
from .帧 import 空浏览器帧
from .导航 import 浏览器导航

__all__=['内嵌帧实现']


class 内嵌帧实现:
    '内嵌帧导航。视图只报告加载，不读跨源内容'

    def __init__(自身,选项,呈现):
        '记下检查点和呈现，并发布带沙箱开关的空状态'
        自身.选项=选项
        自身.呈现=呈现
        自身.导航=浏览器导航(选项.get('initial'))
        自身.已沙箱=True
        自身.错误=None
        自身.已拆除=False
        自身.存储=创建快照存储({**空浏览器帧(),'sandboxEnabled':自身.已沙箱})

        def 设启用(启用):
            '交给这一帧的沙箱开关'
            自身.设沙箱(启用)

        自身.沙箱={'setEnabled':设启用}

    def 处理已加载(自身,修订):
        '记下受控加载，或之后跳到读不到的地址'
        if 自身.已拆除:
            return
        自身.导航.帧已加载(修订)
        自身.发布()

    def 处理加载失败(自身,修订):
        '只给当前这一代文档发布失败'
        请求=自身.导航.快照.get('request')
        if 自身.已拆除 or 请求 is None or 请求['revision']!=修订:
            return
        自身.错误={'code':None,'description':None}
        自身.发布()

    def getSnapshot(自身):
        '当前导航状态'
        return 自身.存储.getSnapshot()

    def subscribe(自身,监听):
        '状态变化时调用，返回退订'
        return 自身.存储.subscribe(监听)

    def 加载地址(自身,目标):
        '加载校验过的地址。提交当前地址则刷新'
        if 自身.已拆除:
            return
        当前=浏览器导航.当前(自身.导航.快照)
        if 当前 is not None and 当前['url']==目标['url']:
            请求=自身.导航.刷新()
        else:
            请求=自身.导航.导航(目标)
        自身.装入(请求)

    def 后退(自身):
        '地址仍已知时，沿应用历史后退'
        if not 自身.已拆除:
            自身.装入(自身.导航.后退())

    def 前进(自身):
        '地址仍已知时，沿应用历史前进'
        if not 自身.已拆除:
            自身.装入(自身.导航.前进())

    def 刷新(自身):
        '重载最后一条已知地址'
        if not 自身.已拆除:
            自身.装入(自身.导航.刷新())

    def 拆除(自身):
        '去掉呈现。再拆一次直接返回'
        if 自身.已拆除:
            return
        自身.已拆除=True
        自身.呈现.拆除()

    def 设沙箱(自身,启用):
        '切换嵌入沙箱。还没有页面时只改状态，否则重载'
        if 自身.已拆除 or 启用==自身.已沙箱:
            return
        自身.已沙箱=启用
        if 自身.存储.getSnapshot()['target'] is None:
            当前=自身.存储.getSnapshot()
            自身.存储.set({**当前,'sandboxEnabled':启用})
            return
        自身.装入(自身.导航.刷新())

    def 装入(自身,请求):
        '清掉旧失败，发布加载中，再把文档交给呈现'
        if 请求 is None:
            return
        自身.错误=None
        自身.发布()
        自身.呈现.展示({
            'target':请求['target'],
            'revision':请求['revision'],
            'sandboxed':自身.已沙箱,
        })

    def 取状态(自身):
        '从历史收成工具栏用的帧状态'
        状态=自身.导航.快照
        目标=浏览器导航.当前(状态)
        if 目标 is None:
            地址='empty'
        elif 状态['navigation']['status']=='unknown':
            地址='unknown'
        else:
            地址='requested'
        return {
            'target':目标,
            'address':地址,
            'loading':状态['navigation']['status']=='loading' and 自身.错误 is None,
            'canGoBack':自身.导航.能后退,
            'canGoForward':自身.导航.能前进,
            'error':自身.错误,
            'sandboxEnabled':自身.已沙箱,
        }

    def 发布(自身):
        '写下帧状态，并把导航记录交给持久化'
        自身.存储.set(自身.取状态())
        自身.选项['persist'](自身.导航.快照)
