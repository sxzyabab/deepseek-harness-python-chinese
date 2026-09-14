
__all__=['向导标题']#仅中文公开名


class 向导标题:#芯片标题视图模型
    """芯片与浮动面板头部：向导签标题文本。"""

    def __init__(自身,用标签信息):
        """用标签信息为 PropsRuntime 钩子。"""
        自身.用标签信息=用标签信息#钩子

    def 渲染(自身):
        """结构树：标题文本。"""
        信息=自身.用标签信息()#标签信息
        签=信息['tab'] if isinstance(信息,dict) else 信息.tab#标签记录
        标题=签['title'] if isinstance(签,dict) else 签.title#标题文本
        return {'type':'text','text':标题}#文本
