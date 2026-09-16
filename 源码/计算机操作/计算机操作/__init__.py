from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from .标识构造 import 计算机操作提供方名#再导出标识构造

__all__=['计算机操作错误','计算机操作登记表','计算机操作提供方名']#仅中文公开名

class 计算机操作错误(Exception):#本包异常基类
    """计算机操作登记失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

class 计算机操作登记表(服务):#独占一个提供方登记位
    """在共享计算机操作服务中拥有一个可选提供方登记。"""
    def __init__(自身,上下文对象):#登记为 computerUse
        """登记为 ctx.computerUse。"""
        super().__init__(上下文对象,'computerUse')#挂到上下文服务名
        自身.登记名=None#当前提供方名
    def 提供方名(自身):#读已登记提供方名
        """已登记提供方名，释放资源期间仍报告该名。"""
        return 自身.登记名#当前名
    def 登记(自身,名称):#占用唯一提供方槽
        """占用唯一提供方槽直到拆除。重复登记即使同名也失败。"""
        if 自身.登记名 is not None:#已有登记
            raise 计算机操作错误('computer use provider "'+自身.登记名+'" is already registered')#重复登记
        def 安装():#写入本登记
            """写入本登记并在拆除时清空。"""
            自身.登记名=名称#占用
            def 拆除():#释放本登记
                """只清掉本次写入的名。"""
                自身.登记名=None#清空
            return 拆除#拆除器
        return 自身.所属上下文.副作用(安装,'computerUse.register()')#副作用标签

default=计算机操作登记表#框架槽
