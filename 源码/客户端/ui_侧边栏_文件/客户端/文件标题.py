
__all__=['文件标题']#仅中文公开名


class 文件标题:#芯片标题视图模型
    """芯片与浮动面板头部：文件夹图标 + 标签标题文本。"""

    def __init__(自身,用标签信息):
        """用标签信息为 PropsRuntime 钩子。"""
        自身.用标签信息=用标签信息#钩子

    def 渲染(自身):
        """结构树：图标 + 标题文本。"""
        信息=自身.用标签信息()#标签信息
        签=信息['tab'] if isinstance(信息,dict) else 信息.tab#标签记录
        标题=签['title'] if isinstance(签,dict) else 签.title#标题文本
        return {#结构树
            'type':'fragment',
            'children':[
                {'type':'FileTypeIcon','kind':'folder','size':16,'className':'titleIcon'},#文件夹图标
                {'type':'text','text':标题},#标题
            ],
        }#结束
