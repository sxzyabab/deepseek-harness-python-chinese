"""耐久会话产物无法无损恢复或迁移时抛出的错误。"""

class 会话格式错误(Exception):#会话格式错误
    """耐久会话产物无法无损恢复或迁移时抛出的错误。"""
    def __init__(自身,消息,原因=None):#构造格式错误
        """记下消息与可选原因。"""
        super().__init__(消息)#消息
        自身.name='SessionFormatError'#固定错误名
        if 原因 is not None:#有cause
            自身.__cause__=原因#挂cause

class 会话格式不支持迁移错误(会话格式错误):#不支持迁移错误
    """可读产物但其已发布源策略无受支持迁移。"""
    def __init__(自身,消息,原因=None):#构造不支持迁移错误
        """记下消息与可选原因。"""
        super().__init__(消息,原因)#基类
        自身.name='SessionFormatUnsupportedMigrationError'#固定错误名
