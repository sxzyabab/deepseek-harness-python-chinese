__all__=('工具团队错误',)#仅中文公开名

class 工具团队错误(Exception):#本包异常基类
    '面向模型的 Agent Teams 工具包错误'
    def __init__(自身,消息):#构造
        '记下英文诊断'
        super().__init__(消息)#基类
        自身.消息=消息#诊断
