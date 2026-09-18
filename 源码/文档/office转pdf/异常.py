"""本包异常基类：分类转换失败，引擎细节留在 cause。"""
__all__=['office转pdf错误']#仅中文公开名

class office转pdf错误(Exception):
    """分类转换失败；引擎细节留在 cause。"""
    def __init__(自身,码,消息,原因=None):
        """记下错误码与英文诊断；可选原因链。"""
        super().__init__(消息)#英文消息
        自身.name='OfficeToPdfError'#固定错误名
        自身.code=码#分类码
        自身.message=消息#诊断
        if 原因 is not None:#有原因
            自身.__cause__=原因#链接
