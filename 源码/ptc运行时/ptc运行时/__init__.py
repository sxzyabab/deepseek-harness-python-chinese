import re
from ...依赖 import cordis
from .类型 import (
    绑定错误类字段,
    绑定命名空间字段,
    运行请求字段,
    运行规格字段,
    运行沙箱字段,
    运行失败字段,
    运行结果字段,
    运行失败种类,
)

__all__=[
    '保留绑定全局','保留错误成员','双下划线成员','可移植保留字','ptc运行时','ptc运行时错误',
    '绑定错误类字段','绑定命名空间字段','运行请求字段','运行规格字段',
    '运行沙箱字段','运行失败字段','运行结果字段','运行失败种类',
]

保留绑定全局=frozenset([
    'console',#Node 日志捕获
    '__dsh_main__','__builtins__','__name__','__debug__',#Python 引导槽
])

保留错误成员=frozenset([
    'name','message','stack',#JS Error
    'args','with_traceback','add_note',#Python 异常协议
])

双下划线成员=re.compile(r'^__.+__\Z')#__x__ 形态

可移植保留字=frozenset([#ECMAScript ∪ Python 保留字
    'await','break','case','catch','class','const','continue','debugger','default','delete','do',
    'else','enum','export','extends','false','finally','for','function','if','import','in',
    'instanceof','new','null','return','super','switch','this','throw','true','try','typeof',
    'var','void','while','with','yield','let','static','implements','interface','package',
    'private','protected','public','arguments','eval',
    'False','None','True','and','as','assert','async','def','del','elif','except','from',
    'global','is','lambda','nonlocal','not','or','pass','raise','match','type','_',
])

class ptc运行时错误(Exception):
    """PTC 运行时约定误用。"""
    def __init__(自身,消息):
        """用原样英文消息构造。"""
        super().__init__(消息)

class ptc运行时(cordis.服务):
    """登记一个 ptcRuntime 实现。程序、预算、中止与基底失败落在运行结果；仅约定误用才拒绝。"""
    def __init__(自身,上下文):
        """登记为 ptcRuntime。"""
        super().__init__(上下文,'ptcRuntime')

    def 语言(自身):
        """run 期望的小写语言标识。"""
        raise NotImplementedError('PtcRuntime.language')

    def 隔离(自身):
        """小写执行基底标识。"""
        raise NotImplementedError('PtcRuntime.isolation')

    def 执行说明(自身):
        """提供方拥有的用法说明。"""
        return ''

    def 沙箱模式(自身):
        """文件政策模式；无围栏则为空。"""
        return None

    def 超时(自身):
        """{defaultMs,maxMs}；不支持覆盖则为空。"""
        return None

    def 解析(自身,请求):
        """验证支持的选项并填入目录与截止。请求是 dict。"""
        raise NotImplementedError('PtcRuntime.resolve')

    def 运行(自身,规格):
        """执行完整输入；程序结局为结果字段。规格是 dict。"""
        raise NotImplementedError('PtcRuntime.run')

default=ptc运行时#框架槽
