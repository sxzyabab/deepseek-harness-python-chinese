__all__=['会话面板']#仅中文公开名


def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画


class 会话面板:
    """把 main 席转发给 main.conversation。属性为 dict。"""

    def __init__(自身,属性=None):
        """记下宿主注入的 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 渲染(自身):
        """渲染会话根子槽。"""
        属性=自身.属性#props
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#席位渲染
        return 渲染槽('main.conversation',{})#转发给会话根
