"""向 typert 注册命令的远程列举与执行贡献。

服务键与命名空间均为 `commands`。
"""
from ...typert.协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=[]#公开面空；TYPERT_REMOTE/default 为框架槽不入表

智能体参数={#agent lookup 参数
    'name':'agent',#源码名
    'wire':'agent',#线路字段
    'source':'lookup',#查找
    'lookup':'agent',#lookup 键
    'codec':严格编解码('Agent'),#编解码
}#结束
作用域={'context':'agent','wire':'agent'}#agent scope
包名='@deepseek-ai/dsh-commands'服务='commands'#服务键
命名空间='commands'#命名空间
类前=包名+'#CommandRuntime.'#调用 id 前缀

列表描述符=调用描述符(#commands/list
    类前+'list',#id
    服务,命名空间,'list',#service/ns/method
    [智能体参数],#parameters
    严格编解码('readonly CommandDescriptor[]'),#result
    {'file':'src/index.ts','line':256,'column':3},#sourceLocation
    作用域=作用域,#scope
)#结束 list

执行描述符=调用描述符(#commands/execute
    类前+'execute',#id
    服务,命名空间,'execute',#service/ns/method
    [#parameters
        智能体参数,#agent
        {'name':'line','wire':'line','source':'json','codec':严格编解码('string')},#命令行
    ],#parameters 结束
    严格编解码('CommandExecution | undefined'),#result
    {'file':'src/index.ts','line':284,'column':3},#sourceLocation
    作用域=作用域,#scope
    取消={'parameter':'signal'},#AbortSignal
)#结束 execute

远程贡献表=远程贡献(包名,[列表描述符,执行描述符])#贡献
TYPERT_REMOTE=远程贡献表#typert框架槽
default=远程贡献表#框架槽
