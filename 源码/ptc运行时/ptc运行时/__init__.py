import re#双下划线成员形态
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .类型 import (#再导出词汇
    绑定错误类字段,#错误类字段
    绑定命名空间字段,#命名空间字段
    运行请求字段,#请求字段
    运行规格字段,#规格字段
    运行沙箱字段,#沙箱字段
    运行失败字段,#失败字段
    运行结果字段,#结果字段
    运行失败种类,#失败种类
)#类型再导出结束

__all__=[#仅中文公开名
    '保留绑定全局','保留错误成员','双下划线成员','可移植保留字','ptc运行时','ptc运行时错误',
    '绑定错误类字段','绑定命名空间字段','运行请求字段','运行规格字段',
    '运行沙箱字段','运行失败字段','运行结果字段','运行失败种类',
]#公开面结束

保留绑定全局=frozenset([#每个后端都拒绝的绑定全局
    'console',#Node 日志捕获
    '__dsh_main__','__builtins__','__name__','__debug__',#Python 引导槽
])#保留全局结束

保留错误成员=frozenset([#每个后端都拒绝的错误成员名
    'name','message','stack',#JS Error
    'args','with_traceback','add_note',#Python 异常协议
])#保留成员结束

双下划线成员=re.compile(r'^__.+__\Z')#__x__ 形态

可移植保留字=frozenset([#ECMAScript ∪ Python 保留字
    'await','break','case','catch','class','const','continue','debugger','default','delete','do',
    'else','enum','export','extends','false','finally','for','function','if','import','in',
    'instanceof','new','null','return','super','switch','this','throw','true','try','typeof',
    'var','void','while','with','yield','let','static','implements','interface','package',
    'private','protected','public','arguments','eval',
    'False','None','True','and','as','assert','async','def','del','elif','except','from',
    'global','is','lambda','nonlocal','not','or','pass','raise','match','type','_',
])#保留字结束

class ptc运行时错误(Exception):#本包异常基类
    """PTC 运行时约定误用。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

class ptc运行时(服务):#PTC 执行能力缝
    """登记一个 ctx.ptcRuntime 实现。程序、预算、中止与基底失败落在运行结果；仅约定误用才拒绝。"""
    def __init__(自身,上下文对象):#登记为 ptcRuntime
        """登记为 ctx.ptcRuntime。"""
        super().__init__(上下文对象,'ptcRuntime')#服务名

    def 语言(自身):#源语言标识
        """run 期望的小写语言标识。"""
        raise NotImplementedError('PtcRuntime.language')#子类必须实现

    def 隔离(自身):#执行基底标识
        """小写执行基底标识。"""
        raise NotImplementedError('PtcRuntime.isolation')#子类必须实现

    def 执行说明(自身):#程序用法说明
        """提供方拥有的用法说明。"""
        return ''#默认空

    def 沙箱模式(自身):#部署文件政策
        """文件政策模式；无围栏则为空。"""
        return None#默认无

    def 超时(自身):#数值截止描述
        """{defaultMs,maxMs}；不支持覆盖则为空。"""
        return None#默认无

    def 解析(自身,请求):#解析选项
        """验证支持的选项并填入目录与截止。请求是 dict。"""
        raise NotImplementedError('PtcRuntime.resolve')#子类必须实现

    def 运行(自身,规格):#执行已解析输入
        """执行完整输入；程序结局为结果字段。规格是 dict。"""
        raise NotImplementedError('PtcRuntime.run')#子类必须实现

default=ptc运行时#框架槽
