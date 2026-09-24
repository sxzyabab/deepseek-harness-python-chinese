from ....存储 import 创建快照存储
from .帧 import 空浏览器帧
from .导航 import 浏览器导航

__all__=['内嵌帧实现']

class 内嵌帧实现:
    """拥有应用已知历史的内嵌帧导航。"""
    def __init__(自身,选项,呈现):
        自身.选项=选项
        自身.呈现=呈现
        自身.导航=浏览器导航(选项['initial'] if 'initial' in 选项 else None)
        自身.存储=创建快照存储({**空浏览器帧(),'sandboxEnabled':True})
        自身.已沙箱=True
        自身.错误=None
        自身.已拆除=False
        自身.拆除任务=None
        def 设沙箱(启用):
            自身._设沙箱(启用)
        自身.沙箱={'setEnabled':设沙箱}

    def 处理已加载(自身,修订):
        if 自身.已拆除:
            return
        自身.导航.帧已加载(修订)
        自身._发布()

    def 处理加载失败(自身,修订):
        请求=自身.导航.快照['request']
        if 自身.已拆除 or 请求 is None or 请求['revision']!=修订:
            return
        自身.错误={'code':None,'description':None}
        自身._发布()

    def 取快照(自身):
        return 自身.存储.getSnapshot()

    def 订阅(自身,监听):
        return 自身.存储.subscribe(监听)

    def 加载地址(自身,目标):
        if 自身.已拆除:
            return
        当前=浏览器导航.当前(自身.导航.快照)
        if 当前 is not None and 当前['url']==目标['url']:
            请求=自身.导航.刷新()
        else:
            请求=自身.导航.导航(目标)
        自身._装入(请求)

    def 后退(自身):
        if not 自身.已拆除:
            自身._装入(自身.导航.后退())

    def 前进(自身):
        if not 自身.已拆除:
            自身._装入(自身.导航.前进())

    def 刷新(自身):
        if not 自身.已拆除:
            自身._装入(自身.导航.刷新())

    def 拆除(自身):
        if 自身.拆除任务 is not None:
            return 自身.拆除任务
        自身.已拆除=True
        自身.呈现.拆除()
        class 已完成:
            def 等待(完成自身):
                return None
        自身.拆除任务=已完成()
        return 自身.拆除任务

    def _设沙箱(自身,启用):
        if 自身.已拆除 or 启用==自身.已沙箱:
            return
        自身.已沙箱=启用
        if 自身.存储.getSnapshot()['target'] is None:
            自身.存储.set({**自身.存储.getSnapshot(),'sandboxEnabled':启用})
            return
        自身._装入(自身.导航.刷新())

    def _装入(自身,请求):
        if 请求 is None:
            return
        自身.错误=None
        自身._发布()
        自身.呈现.展示({'target':请求['target'],'revision':请求['revision'],'sandboxed':自身.已沙箱})

    def _快照(自身):
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
            'canGoBack':自身.导航.可后退属性,
            'canGoForward':自身.导航.可前进属性,
            'error':自身.错误,
            'sandboxEnabled':自身.已沙箱,
        }

    def _发布(自身):
        自身.存储.set(自身._快照())
        自身.选项['persist'](自身.导航.快照)

    getSnapshot=取快照
    subscribe=订阅
    loadUrl=加载地址
    goBack=后退
    goForward=前进
    reload=刷新
    dispose=拆除

    @property
    def sandbox(自身):
        return 自身.沙箱
