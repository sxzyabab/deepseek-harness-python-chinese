class 原生命令错误(Exception):
    '宿主原生命令失败，附加码与捕获输出'
    def __init__(自身,消息,码,标准输出,标准错误,原因):
        '把退出/系统码与两路捕获输出挂到异常上'
        super().__init__(消息)
        自身.code=码
        自身.stdout=标准输出
        自身.stderr=标准错误
        自身.cause=原因
