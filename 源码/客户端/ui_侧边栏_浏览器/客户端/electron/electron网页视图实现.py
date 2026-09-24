import threading
from ....存储 import 创建快照存储
from ..浏览器.帧 import 空浏览器帧
from ..浏览器.浏览器持久化 import 浏览器地址检查点,当前浏览器目标
from ..浏览器.地址 import 解析浏览器地址

__all__=['electron网页视图实现']

def 已中止(信号):
    if 信号 is None:
        return False
    return 信号.is_set()

class electron网页视图实现:
    """拥有原生历史并把桌面观察译成公共帧态。"""
    def __init__(自身,选项,桥,工作区,呈现):
        自身.选项=选项
        自身.桥=桥
        自身.工作区=工作区
        自身.呈现=呈现
        自身.寿命=threading.Event()
        自身.存储=创建快照存储(空浏览器帧())
        自身.检查点=当前浏览器目标(选项['initial'] if 'initial' in 选项 else None)
        自身.宾客寿命=None
        自身.元素=None
        自身.租约=None
        自身.工作区键=None
        自身.初始化中=None
        自身.就绪=False
        自身.待发=None
        自身.修订=0
        自身.首文档=True
        自身.拆除任务=None
        自身.附着信号=None
        自身.释放表=set()

    def 取快照(自身):
        return 自身.存储.getSnapshot()

    def 订阅(自身,监听):
        return 自身.存储.subscribe(监听)

    def 附着(自身):
        if 自身.寿命.is_set():
            return
        自身.附着信号=threading.Event()
        当前=自身.存储.getSnapshot()
        if 自身.待发 is None:
            自身.待发=当前['target']
        if 自身.待发 is not None:
            自身.存储.set({**当前,'address':'requested','loading':True,'canGoBack':False,'canGoForward':False,'error':None})
            自身._初始化()

    def 脱离(自身):
        if 自身.附着信号 is not None:
            自身.附着信号.set()
        自身.附着信号=None
        自身.待发=自身.存储.getSnapshot()['target']
        自身._丢宾客()

    def 加载地址(自身,目标):
        if 自身.寿命.is_set():
            return
        当前=自身.存储.getSnapshot()
        if 自身.就绪 and 当前['address']=='observed' and 当前['target'] is not None and 当前['target']['url']==目标['url']:
            自身.刷新()
            return
        自身.修订+=1
        自身.待发=目标
        自身.存储.set({**当前,'target':目标,'address':'requested','loading':True,'error':None})
        自身._持久化(目标)
        if 自身.就绪:
            自身._装待发()
        else:
            自身._初始化()

    def 后退(自身):
        if 自身.存储.getSnapshot()['canGoBack']:
            自身._导航('goBack')

    def 前进(自身):
        if 自身.存储.getSnapshot()['canGoForward']:
            自身._导航('goForward')

    def 刷新(自身):
        当前=自身.存储.getSnapshot()
        if 自身.寿命.is_set() or 当前['target'] is None:
            return
        if not 自身.就绪 or 当前['error'] is not None:
            自身.修订+=1
            自身.待发=当前['target']
            自身.存储.set({**当前,'loading':True,'error':None})
            if 自身.就绪:
                自身._装待发()
            else:
                自身._初始化()
        else:
            自身._导航('reload')

    def 拆除(自身):
        if 自身.拆除任务 is not None:
            return 自身.拆除任务
        自身.寿命.set()
        自身.待发=None
        自身._丢宾客()
        自身.呈现.拆除()
        class 已完成:
            def 等待(完成自身):
                return None
        自身.拆除任务=已完成()
        return 自身.拆除任务

    def _导航(自身,命令):
        if 自身.寿命.is_set() or not 自身.就绪 or 自身.元素 is None:
            return
        自身.修订+=1
        自身.待发=None
        自身.存储.set({**自身.存储.getSnapshot(),'loading':True,'error':None})
        动作=自身.元素[命令] if 命令 in 自身.元素 else None
        if 动作 is None:
            return
        try:
            动作()
        except Exception as 错误:
            自身._命令失败(错误)

    def _初始化(自身):
        附着=自身.附着信号
        if 附着 is None or 自身.初始化中 is not None or 自身.元素 is not None or 自身.寿命.is_set():
            return
        def 跑():
            try:
                自身._创建宾客(附着)
            except Exception as 错误:
                自身._丢宾客()
                if not 已中止(附着) and not 自身.寿命.is_set():
                    自身._命令失败(错误)
            finally:
                自身.初始化中=None
                if 自身.附着信号 is not 附着 and 自身.待发 is not None:
                    自身._初始化()
        自身.初始化中=threading.Thread(target=跑,daemon=True)
        自身.初始化中.start()

    def _创建宾客(自身,附着信号):
        if 自身.工作区键 is None:
            键=自身.工作区(附着信号)
            if hasattr(键,'等待'):
                键=键.等待()
            自身.工作区键=键
        if 已中止(附着信号):
            return
        预约=自身.桥.acquire(自身.工作区键)
        if hasattr(预约,'等待'):
            预约=预约.等待()
        if 已中止(附着信号):
            自身._释放(预约['lease'] if isinstance(预约,dict) else 预约.lease)
            return
        自身.租约=预约['lease'] if isinstance(预约,dict) else 预约.lease
        自身.宾客寿命=threading.Event()
        元素=自身.呈现.创建元素(预约 if isinstance(预约,dict) else {'partition':预约.partition,'lease':预约.lease})
        自身.元素=元素
        def 打开(网址):
            if 自身.元素 is 元素 and not 已中止(附着信号) and not 自身.宾客寿命.is_set():
                自身.选项['openRequested'](网址)
        退开=自身.桥.onOpenRequested(自身.租约,打开)
        自身.就绪=True
        自身._装待发()
        自身.呈现.呈现(元素)
        return 退开

    def _装待发(自身):
        目标=自身.待发
        元素=自身.元素
        if not 自身.就绪 or 目标 is None or 元素 is None:
            return
        自身.待发=None
        装=元素['loadURL'] if 'loadURL' in 元素 else None
        if 装 is None:
            return
        try:
            装(目标['url'])
        except Exception as 错误:
            码=错误.code if hasattr(错误,'code') else None
            if 码=='ERR_ABORTED':
                return
            if 自身.存储.getSnapshot()['error'] is None:
                自身._命令失败(错误)

    def _持久化(自身,目标):
        点=自身.检查点
        if 点 is not None and 目标['url']==点['url'] and 目标['title']==点['title']:
            return
        自身.检查点=目标
        自身.选项['persist'](浏览器地址检查点(目标,自身.修订))

    def _失败(自身,错误=None):
        if 自身.寿命.is_set():
            return
        if 错误 is None:
            错误={'code':None,'description':None}
        当前=自身.存储.getSnapshot()
        自身.存储.set({**当前,'loading':False,'error':错误,'canGoBack':自身.就绪 and 当前['canGoBack'],'canGoForward':自身.就绪 and 当前['canGoForward']})

    def _命令失败(自身,错误):
        print('Desktop browser operation failed',错误)
        自身._失败()

    def _丢宾客(自身):
        if 自身.宾客寿命 is not None:
            自身.宾客寿命.set()
        自身.宾客寿命=None
        自身.呈现.清空()
        自身.元素=None
        自身.就绪=False
        自身.首文档=True
        租约=自身.租约
        自身.租约=None
        if 租约 is not None:
            自身._释放(租约)

    def _释放(自身,租约):
        try:
            自身.桥.release(租约)
        except Exception as 错误:
            print('Desktop browser guest release failed',错误)

    getSnapshot=取快照
    subscribe=订阅
    attach=附着
    detach=脱离
    loadUrl=加载地址
    goBack=后退
    goForward=前进
    reload=刷新
    dispose=拆除
