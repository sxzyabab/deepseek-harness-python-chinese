__all__=['客户端运行时执行错误']#仅中文公开名

class 客户端运行时执行错误(Exception):#Client运行时执行错误
    """经类型化 Client Runtime 错误结果返回的失败。"""
    def __init__(自身,code,message):#绑定错误码
        """保存错误码与信息。"""
        super().__init__(message)#基类消息
        自身.code=code#错误码
        自身.message=message#信息
