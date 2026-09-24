__all__=['文件标题']

#
class 文件标题:
    """芯片与浮动面板头部：文件夹图标加标签标题。"""

    def __init__(自身,用标签信息):
        """用标签信息为运行时钩子，调用时才读当前标签。"""
        自身.用标签信息=用标签信息

    def 渲染(自身):
        """结构树。标签记录跨边界时是 dict，包内铸造时是对象。"""
        信息=自身.用标签信息()
        签=信息['tab'] if isinstance(信息,dict) else 信息.tab
        标题=签['title'] if isinstance(签,dict) else 签.title
        return {
            'type':'fragment',
            'children':[
                {'type':'FileTypeIcon','kind':'folder','size':16,'className':'titleIcon'},
                {'type':'text','text':标题},
            ],
        }
