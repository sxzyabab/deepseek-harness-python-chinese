__all__=('命令错误','启动错误')#仅中文公开名

class 命令错误(Exception):
    '帮助、版本、解析错误或程序主动拒绝时抛出；携带退出码'
    def __init__(自身,消息,退出码=1,码='commander.error'):
        '记下消息、退出码与错误码'
        super().__init__(消息)#消息
        自身.exitCode=退出码#退出码
        自身.code=码#错误码前缀 commander.*

class 启动错误(Exception):
    '启动器未提供命令行服务或程序未声明 action'
