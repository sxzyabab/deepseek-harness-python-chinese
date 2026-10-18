'从页面注入的访问快照起步，跟随本对等端的快照流'
from ..快照 import 远程访问快照键#注入全局名
from .挂载 import 挂载访问#挂载与跟随
from .状态 import 解析注入基线#校验注入基线

依赖=['remote','slots']#远程面与槽登记
inject=依赖#框架槽

def 应用(上下文,配置=None):
    '挂载生成的 remoteAccess 命名空间并发布访问钩子'
    注入=getattr(上下文,'globalThis',None)#测试可替换
    值=None if 注入 is None else 注入.get(远程访问快照键)#页面注入
    if 值 is None:#读进程全局
        import builtins#页面脚本注入的全局
        值=getattr(builtins,远程访问快照键,None)#没有则空
    return 挂载访问(上下文,None,解析注入基线(值))#没有生成贡献时由调用方以后替换

__all__=['依赖','应用','apply']
apply=应用#框架槽
