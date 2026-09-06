"""工作区控制器远程错误与中止查询。

对齐上游工作区控制器杂物袋：RemoteError 与 Abort 查询。公开面仅中文名。
"""
__all__=['远程错误','远程错误消息','已中止','若已中止则抛出']#仅中文公开名

class 远程错误(Exception):
    """对齐上游 RemoteError。附加信息做成属性。"""
    def __init__(自身,码,消息,详情=None,原因=None):
        """记下 code/message/details。"""
        super().__init__(消息)#消息
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details={} if 详情 is None else 详情#详情
        if 原因 is not None:#原因链
            自身.__cause__=原因#链接

def 远程错误消息(错误):
    """把错误收成字符串。"""
    return str(错误)#消息

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 置位

def 若已中止则抛出(信号):
    """已中止则抛出取消。"""
    if 已中止(信号):#已中止
        raise 远程错误('gateway/cancelled','aborted',{})#取消
