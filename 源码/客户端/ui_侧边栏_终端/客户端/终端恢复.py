from ...模块.客户端.通告 import 取握手窗口

__all__=['终端恢复']

class 终端恢复:
    '显示会话时恢复终端。失败给重试'
    def __init__(自身,属性=None):
        '记下份额并立刻恢复'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.错误=None
        自身.尝试=0
        自身.存活=True
        自身.根=None
        自身.恢复()

    def 更新(自身,属性):
        '换上一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 卸载(自身):
        '随后到达的结果不再画'
        自身.存活=False

    def 恢复(自身):
        '失败记下说明'
        try:
            自身.属性['restore']()
            if 自身.存活:
                自身.错误=None
        except Exception as 错误:
            if 自身.存活:
                自身.错误=str(错误)
        if 自身.存活:
            自身.渲染()

    def 渲染(自身):
        '成功没有节点。失败是重试按钮'
        if isinstance(自身.属性,dict) and 自身.属性.get('window') is not None:
            窗=自身.属性['window']
        else:
            窗=取握手窗口()
        文档=窗.document
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        if 自身.错误 is None:
            return None

        def 点击(事件):
            '清掉错误再恢复一次'
            自身.错误=None
            自身.尝试=自身.尝试+1
            自身.恢复()

        钮=文档.createElement('button')
        钮.type='button'
        钮.setAttribute('title','恢复终端失败：'+自身.错误)
        钮.textContent='重试恢复终端'
        钮.addEventListener('click',点击)
        自身.根=钮
        父=自身.属性.get('parent')
        if 父 is not None:
            父.appendChild(钮)
        return 钮

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
