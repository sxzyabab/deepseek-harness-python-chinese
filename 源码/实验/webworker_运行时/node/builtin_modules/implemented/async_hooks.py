from ...未实现失败 import 未实现失败,运行时错误

__all__=[
    'executionAsyncId','triggerAsyncId','createHook','AsyncResource',
    'AsyncLocalStorage','__esModule','default',
]

实例集合=set()

class 异步本地存储:
    """Node 的 AsyncLocalStorage 面，收窄到宿主树所用成员。"""

    def __init__(自身):
        """登记实例并清空各槽。"""
        自身._条目列表=[]
        自身._覆盖=None
        自身._环境列表=[]
        自身._已恢复=None
        实例集合.add(自身)

    def run(自身,存储,回调,*参数):
        """在操作整个寿命内以可见存储运行回调。"""
        条目={'store':存储}
        自身._条目列表.append(条目)

        def 移除():
            """按项身份移除。"""
            for 下标 in range(len(自身._条目列表)-1,-1,-1):
                if 自身._条目列表[下标] is 条目:
                    自身._条目列表.pop(下标)
                    return

        环境={'store':存储}
        自身._环境列表.append(环境)

        def 卸边界():
            """卸环境与折叠项，并恢复先前恢复槽。"""
            for 下标 in range(len(自身._环境列表)-1,-1,-1):
                if 自身._环境列表[下标] is 环境:
                    自身._环境列表.pop(下标)
                    break
            if 自身._已恢复 is None: 自身._已恢复=恢复已恢复
            移除()

        恢复覆盖=自身._覆盖
        恢复已恢复=自身._已恢复
        自身._覆盖=None
        自身._已恢复=None
        try:
            结果=回调(*参数)
        except BaseException:
            自身._覆盖=恢复覆盖
            卸边界()
            raise
        自身._覆盖=恢复覆盖
        卸边界()
        return 结果

    def getStore(自身):
        """按槽序解析当前存储。"""
        if 自身._覆盖 is not None: return 自身._覆盖['store']
        if 自身._已恢复 is not None: return 自身._已恢复['store']
        if len(自身._环境列表)>0: return 自身._环境列表[-1]['store']
        if len(自身._条目列表)>0: return 自身._条目列表[-1]['store']
        return None

    def exit(自身,回调,*参数):
        """以无存储运行回调。"""
        return 自身.run(None,回调,*参数)

    def enterWith(自身,存储):
        """进入持续到 disable 的边界。"""
        自身._条目列表.append({'store':存储})

    def disable(自身):
        """丢掉每个槽。"""
        自身._条目列表.clear()
        自身._覆盖=None
        自身._环境列表.clear()
        自身._已恢复=None

    @staticmethod
    def 快照全部():
        """复制每个活动实例的有效存储。"""
        return [{'instance':实例,'store':实例.getStore()} for 实例 in 实例集合]

    @staticmethod
    def 恢复全部(快照):
        """把快照安装为其所点名每个实例的环境上下文。"""
        已装=[]
        for 项 in 快照:
            实例=项['instance']
            槽={'store':项['store']}
            先前=实例._已恢复
            实例._已恢复=槽
            已装.append({'instance':实例,'slot':槽,'before':先前})

        def 拆除():
            """按身份检查后恢复先前环境。"""
            for 记录 in 已装:
                if 记录['instance']._已恢复 is 记录['slot']:
                    记录['instance']._已恢复=记录['before']
        return 拆除

    @staticmethod
    def 捕获上下文():
        """复制每个活动实例的当前存储；全空时为 None。"""
        捕获=None
        for 实例 in 实例集合:
            存储=实例.getStore()
            if 存储 is None: continue
            if 捕获 is None: 捕获=[]
            捕获.append({'instance':实例,'store':存储})
        return 捕获

    @staticmethod
    def 带上下文运行(快照,回调):
        """把捕获上下文恢复进覆盖槽后运行回调。"""
        if 快照 is None: return 回调()
        先前列表=[]
        for 项 in 快照:
            实例=项['instance']
            先前=实例._覆盖
            实例._覆盖={'store':项['store']}
            先前列表.append({'instance':实例,'before':先前})
        try:
            return 回调()
        finally:
            for 记录 in 先前列表:
                记录['instance']._覆盖=记录['before']

    @staticmethod
    def 列出活动实例():
        """每个活动实例。"""
        return list(实例集合)

    @staticmethod
    def bind(回调):
        """把回调绑定到当前上下文。"""
        return 绑定异步上下文(回调)

    @staticmethod
    def snapshot():
        """匹配 Node 静态面的快照辅助。"""
        快照=异步本地存储.捕获上下文()
        def 恢复器(回调):
            """在捕获上下文中运行。"""
            return 异步本地存储.带上下文运行(快照,回调)
        return 恢复器

def 捕获异步上下文():
    """复制每个活动实例的当前存储。"""
    return 异步本地存储.捕获上下文()

def 在异步上下文运行(快照,回调):
    """把捕获上下文恢复进覆盖槽后运行回调。"""
    return 异步本地存储.带上下文运行(快照,回调)

def 绑定异步上下文(回调):
    """此刻捕获当前上下文，并在每次后续调用周围恢复。"""
    快照=捕获异步上下文()
    if 快照 is None: return 回调
    def 已绑定(*参数):
        """恢复后调用。"""
        def 调用():
            """调用原回调。"""
            return 回调(*参数)
        return 在异步上下文运行(快照,调用)
    return 已绑定

def 在异步上下文根运行(回调):
    """在根处运行回调：每个实例读 None。"""
    根=[{'instance':实例,'store':None} for 实例 in 异步本地存储.列出活动实例()]
    return 在异步上下文运行(根,回调)

def 快照全部():
    """加载器 await 改写的暂停点。"""
    return 异步本地存储.快照全部()

def 恢复全部(快照):
    """加载器 await 改写的恢复点。"""
    return 异步本地存储.恢复全部(快照)

def 快照面():
    """暂停。"""
    return 快照全部()

def 恢复面(快照):
    """恢复（丢弃拆除器）。"""
    恢复全部(快照)

als因果={
    'snapshot':快照面,
    'restore':恢复面,
}

def executionAsyncId():
    """不跟踪 async id；稳定 id 让记录它的调用方仍能工作。"""
    return 1

def triggerAsyncId():
    """亦不跟踪 trigger id。"""
    return 0

def createHook(*位置参数,**关键字参数):
    """无法创建异步钩子：worker 中无异步资源跟踪。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:async_hooks.createHook')

AsyncResource=未实现失败('node:async_hooks','AsyncResource')
AsyncLocalStorage=异步本地存储
__snapshotAll=快照全部
__restoreAll=恢复全部
alsCausality=als因果
__esModule=True

default={
    'AsyncLocalStorage':异步本地存储,'AsyncResource':AsyncResource,
    'executionAsyncId':executionAsyncId,'triggerAsyncId':triggerAsyncId,'createHook':createHook,
}
