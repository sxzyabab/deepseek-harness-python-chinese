from dataclasses import dataclass as 数据类

@数据类
class 权限:
    创建文件:bool
    删除文件:bool
    修改文件:bool
    读取文件:bool


class 统一文件工具审批:
    def __init__(self,权限):
        ...

    ...