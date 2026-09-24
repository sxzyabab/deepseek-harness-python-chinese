from .模型 import 客户端作业模型
from .服务 import 客户端作业

__all__=['依赖','应用','默认','客户端作业','客户端作业模型']

依赖=['remote','remote.job']

def 应用(上下文):
    """安装客户端作业服务。"""
    远程面=上下文.remote
    客户端作业(上下文,{'$stream':远程面.$stream,'job':远程面.job},客户端作业模型())

inject=依赖
apply=应用
default=应用
默认=应用
