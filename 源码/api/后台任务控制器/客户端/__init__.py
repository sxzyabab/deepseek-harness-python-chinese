'客户端作业：在 remote.job 上安装名册、观察和人类终止'
from ....基础设施.通用工具 import 获取内部数据#取出 remote 上的 $stream
from . import (#同目录模块，导入即执行顶层
    服务,#名册、观察与终止
    模型,#快照
)

__all__=['依赖','应用','服务','模型']

依赖=['remote','remote.job']#客户端远程与 job 命名空间

def 应用(上下文,配置=None):
    '安装客户端作业服务。现在就取出 job 面，流重开的调用栈上没有声明 remote.job'
    远程面=上下文.remote#客户端远程
    作业面=远程面.job#job 命名空间
    流工厂=获取内部数据(远程面,'stream')#$stream
    服务.客户端作业(上下文,{'$stream':流工厂,'job':作业面},模型.客户端作业模型())#装上 jobs

inject=依赖#框架槽
apply=应用#框架槽
