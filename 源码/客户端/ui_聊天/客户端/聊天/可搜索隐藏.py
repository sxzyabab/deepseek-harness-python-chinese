__all__=['可搜索隐藏','可搜索隐藏席']


class 可搜索隐藏席:
    '不卸掉子树，只切换可搜索的 hidden。有过渡时先动画再提交属性'
    def __init__(自身,隐藏,揭示,过渡=None):
        '记下目标和可选的折叠过渡'
        自身.隐藏=隐藏
        自身.揭示=揭示
        自身.过渡=过渡
        自身.元素=None
        自身.已听=False

    def 准备(自身,隐藏,揭示):
        '同一次渲染里更新目标和揭示回调'
        自身.隐藏=隐藏
        自身.揭示=揭示

    def 绑(自身,元素):
        '挂到稳定根上，并听浏览器查找的 beforematch'
        if 元素 is None:
            return None
        if 自身.元素 is not 元素:
            自身.已听=False
            自身.元素=元素
        if not 自身.已听:
            def 匹配前(事件=None):
                '查找命中隐藏内容时展开'
                自身.揭示()
            元素.addEventListener('beforematch',匹配前)
            自身.已听=True
        自身.应用()
        return 元素

    def 应用(自身):
        '焦点还在里面就先揭示。否则提交 until-found 或拿掉 hidden'
        元素=自身.元素
        if 元素 is None:
            return
        文档=getattr(元素,'ownerDocument',None)
        活动=getattr(文档,'activeElement',None) if 文档 is not None else None
        if 自身.隐藏 and 活动 is not None and 元素.contains(活动):
            自身.揭示()
            return

        def 提交():
            '最终可见性。隐藏用 until-found，方便页内查找'
            if 自身.隐藏:
                元素.setAttribute('hidden','until-found')
            else:
                元素.removeAttribute('hidden')

        if 自身.过渡 is None:
            提交()
        else:
            自身.过渡(元素,自身.隐藏,提交)

    def 渲染(自身):
        '旧席位：有 window 时造根，再套用隐藏'
        if 自身.元素 is None and getattr(自身,'window',None) is not None:
            自身.元素=自身.window.document.createElement('div')
        自身.根=自身.元素
        自身.应用()
        return 自身.根


def 可搜索隐藏(隐藏,揭示,过渡=None):
    '造一份可搜索隐藏席'
    return 可搜索隐藏席(隐藏,揭示,过渡)
