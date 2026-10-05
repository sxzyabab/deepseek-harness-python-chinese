from dataclasses import dataclass as 数据类

@数据类
class 权限配置:
    创建文件:bool
    删除文件:bool
    修改文件:bool
    读取文件:bool
    ...

@数据类
class 权限描述:
    必须人类审批:bool
    可并发:bool #false表示必须串行,部分并发类工具设为True串行部分内部解决
    幂等:bool
    可撤销:bool #回滚等使用


class 统一文件工具审批:
    def __init__(self,权限):
        ...

    ...