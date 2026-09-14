
__all__=['右栏根']#仅中文公开名


class 右栏根:#右栏根视图模型
    """渲染 `rightbar.session` 子席。"""

    def __init__(自身,渲染会话=None,**_属性):
        """渲染会话为子席渲染器。"""
        自身.渲染会话=渲染会话#子席

    def 渲染(自身):
        """结构树：会话子席。"""
        if 自身.渲染会话 is None:#无
            return {'type':'fragment','children':[]}#空
        return 自身.渲染会话()#会话
