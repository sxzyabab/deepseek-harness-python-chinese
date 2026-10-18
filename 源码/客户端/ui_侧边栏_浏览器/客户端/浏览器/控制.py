from ....存储 import 创建快照存储
from .浏览器持久化 import 当前浏览器目标
from .地址 import 解析浏览器地址

__all__=['浏览器控制器']


class 浏览器控制器:
    '校验地址并持有一页的寿命，不看具体载体'

    def __init__(自身,选项):
        '按身份、持久化和页工厂建页，并跟上帧状态'
        自身.选项=选项
        自身.动作=选项['actions']
        自身.检查点=选项.get('initial')
        自身.已开始=False
        自身.已拆除=False

        def 持久(状态):
            '页还在就记下检查点并写入存储'
            if 自身.已拆除:
                return
            自身.检查点=状态
            自身.动作['replace'](选项['tabId'],状态)

        def 打开请求(值):
            '来自页面的打开请求先过地址校验'
            if 自身.已拆除:
                return
            结果=解析浏览器地址(值,选项['applicationOrigin'])
            if not 结果['ok']:
                自身.地址失败(结果['reason'])
                return
            选项['openTab'](结果['target']['url'])

        自身.页=选项['createPage']({
            'initial':选项.get('initial'),
            'persist':持久,
            'openRequested':打开请求,
        })
        自身.存储=创建快照存储({
            'frame':自身.页['frame'].getSnapshot(),
            'restoreTarget':当前浏览器目标(自身.检查点),
            'addressFailure':None,
            'addressRevision':0,
        })

        def 帧变了():
            '帧状态变了就改工具栏状态。地址变了就清掉校验失败并抬修订'
            if 自身.已拆除:
                return
            当前=自身.存储.getSnapshot()
            帧=自身.页['frame'].getSnapshot()
            旧目标=当前['frame'].get('target')
            新目标=帧.get('target')
            旧址=None if 旧目标 is None else 旧目标.get('url')
            新址=None if 新目标 is None else 新目标.get('url')
            变了=旧址!=新址
            if 帧.get('target') is None:
                恢复=当前浏览器目标(自身.检查点)
            else:
                恢复=None
            自身.存储.set({
                'frame':帧,
                'restoreTarget':恢复,
                'addressFailure':None if 变了 else 当前['addressFailure'],
                'addressRevision':当前['addressRevision']+(1 if 变了 else 0),
            })

        自身.退订=自身.页['frame'].subscribe(帧变了)

        def 中止():
            '标签寿命结束就拆掉这一页'
            自身.拆除()

        自身.中止=中止
        选项['signal'].addEventListener('abort',中止,{'once':True})

    def getSnapshot(自身):
        '工具栏用的当前状态'
        return 自身.存储.getSnapshot()

    def subscribe(自身,监听):
        '状态变化时调用，返回退订'
        return 自身.存储.subscribe(监听)

    def 挂载(自身,视口标识):
        '把页附到内容容器。返回的函数只结束附着'
        自身.发布已存()
        return 自身.页['presentation'].挂载(视口标识)

    def 开始(自身,初始地址):
        '显式打开地址只消费一次。只有检查点时不自己打开'
        if 自身.已开始 or 自身.已拆除:
            return
        自身.已开始=True
        if 初始地址 is not None:
            自身.加载地址(初始地址)

    def 恢复(自身):
        '只有用户要求恢复时才加载保存的地址'
        目标=自身.存储.getSnapshot().get('restoreTarget')
        if 目标 is not None:
            自身.加载地址(目标['url'])

    def 加载地址(自身,值):
        '先校验再导航。无效输入留给界面改正'
        if 自身.已拆除:
            return
        解析=解析浏览器地址(值,自身.选项['applicationOrigin'])
        if not 解析['ok']:
            自身.地址失败(解析['reason'])
            return

        def 执行():
            '把校验过的目标交给页'
            自身.页['frame'].加载地址(解析['target'])

        自身.执行(执行)

    def 后退(自身):
        '把后退交给页'
        def 执行():
            '后退'
            自身.页['frame'].后退()

        自身.执行(执行)

    def 前进(自身):
        '把前进交给页'
        def 执行():
            '前进'
            自身.页['frame'].前进()

        自身.执行(执行)

    def 刷新(自身):
        '有待恢复的地址就恢复，否则重载已经请求的页'
        if 自身.存储.getSnapshot().get('restoreTarget') is not None:
            自身.恢复()
            return

        def 执行():
            '重载'
            自身.页['frame'].刷新()

        自身.执行(执行)

    def 设沙箱(自身,启用):
        '有嵌入沙箱开关才应用。没有的载体保持原样'
        沙箱=getattr(自身.页['frame'],'沙箱',None)
        if 沙箱 is None:
            return

        def 执行():
            '切换沙箱'
            沙箱['setEnabled'](启用)

        自身.执行(执行)

    def 重绑(自身,动作):
        '之后的检查点写到替换后的会话绑定'
        自身.动作=动作

    def 拆除(自身):
        '放开页，并摘掉寿命和状态订阅。再拆一次直接返回'
        if 自身.已拆除:
            return
        自身.已拆除=True
        自身.选项['signal'].removeEventListener('abort',自身.中止)
        自身.退订()
        自身.页['frame'].拆除()

    def 发布已存(自身):
        '挂载时把已有检查点写回存储'
        if 自身.检查点 is not None:
            自身.动作['replace'](自身.选项['tabId'],自身.检查点)

    def 地址失败(自身,原因):
        '留下这次地址拒绝，不抬修订'
        自身.存储.set({**自身.存储.getSnapshot(),'addressFailure':原因})

    def 执行(自身,运行):
        '清掉地址错误并抬修订，再跑导航'
        if 自身.已拆除:
            return
        当前=自身.存储.getSnapshot()
        自身.存储.set({
            **当前,
            'addressFailure':None,
            'addressRevision':当前['addressRevision']+1,
        })
        运行()
