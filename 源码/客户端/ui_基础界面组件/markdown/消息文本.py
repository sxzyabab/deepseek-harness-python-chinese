__all__=['消息文本']#仅中文公开名

class 消息文本:#字面文本
    """结构化视图。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """产出文本块。"""
        文=自身.属性['text'] if 'text' in 自身.属性 and 自身.属性['text'] is not None else ''#正文
        return {#视图
            'type':'message-text',#类型
            'text':文,#正文
            'cssModule':'消息文本.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
