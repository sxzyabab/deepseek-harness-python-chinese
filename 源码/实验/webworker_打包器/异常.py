__all__=('打包器错误',)#仅中文公开名

class 打包器错误(Exception):#本包异常基类
    'webworker 打包器包内错误基类'
    def __init__(自身,消息):#构造
        '记下英文诊断'
        super().__init__(消息)#基类
        自身.消息=消息#诊断
