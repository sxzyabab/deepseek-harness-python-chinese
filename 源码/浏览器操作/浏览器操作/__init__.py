from ...依赖 import cordis
服务=cordis.服务
from .标识构造 import 浏览器操作提供方名

__all__=['浏览器操作错误','浏览器操作登记表','浏览器操作提供方名']

class 浏览器操作错误(Exception):
    """浏览器操作登记失败。"""
    def __init__(自身,消息):
        """用原样英文消息构造。"""
        super().__init__(消息)

class 浏览器操作登记表(服务):
    """在共享浏览器操作服务中拥有一个可选提供方登记。"""
    def __init__(自身,上下文):
        """登记为 browserUse。"""
        super().__init__(上下文,'browserUse')
        自身.登记名=None
    def 提供方名(自身):
        """已登记提供方名，释放资源期间仍报告该名。"""
        return 自身.登记名
    def 登记(自身,名称):
        """占用唯一提供方槽直到拆除。重复登记即使同名也失败。"""
        if 自身.登记名 is not None:
            raise 浏览器操作错误('browser use provider "'+自身.登记名+'" is already registered')
        def 安装():
            """写入本登记并在拆除时清空。"""
            自身.登记名=名称
            def 拆除():
                """只清掉本次写入的名。"""
                自身.登记名=None
            return 拆除
        return 自身.所属上下文.副作用(安装,'browserUse.register()')

default=浏览器操作登记表#框架槽
