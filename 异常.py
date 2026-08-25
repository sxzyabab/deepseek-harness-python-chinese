#errors.py
from __future__ import annotations

class Harness错误(Exception):
    "SDK与运行时失败的基类异常"

class 传输层关闭错误(Harness错误):
    "运行时子进程退出或关闭标准输出时抛出"

class SDK协议错误(Harness错误):
    "运行时发送了超出SDK协议范围的数据时抛出"

class JSON_RPC错误(Harness错误):
    "运行时返回JSON-RPC错误响应时抛出"
    def __init__(self,code:int|None,message:str,data:object|None=None)->None:
        super().__init__(message)
        self.code=code
        self.message=message
        self.data=data

#python原生版专属
class cordis错误(Exception):
    ...

class 插件接口错误(cordis错误):
    ...