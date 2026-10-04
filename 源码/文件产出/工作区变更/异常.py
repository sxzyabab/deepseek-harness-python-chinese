class 工作区变更错误(Exception):#本包异常基类
    '工作区变更插件入参或运行失败'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

class 记录器错误(Exception):#本模块异常
    '轮次记录失败'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

class 版本库错误(Exception):#本包git异常
    'git 命令失败或输出越界'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

class 捕获错误(Exception):#本模块异常
    '捕获读写失败'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

class 行数统计错误(Exception):#本模块异常
    '行数统计输出畸形'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息
