'终端控制器的视图失败'
from ...类型化远程调用.协议 import 远程错误#线路上的 code/message/details

__all__=['终端视图错误']#异常类留在本文件


class 终端视图错误(远程错误):
    '客户端终端失败。code 为 terminal/view，details.issue 为产品键'
    def __init__(自身,问题,消息=None):
        '缺省消息就是问题键'
        if 消息 is None:#未另给说明
            消息=问题#用问题键
        super().__init__('terminal/view',消息,{'issue':问题})#构造远程错误
