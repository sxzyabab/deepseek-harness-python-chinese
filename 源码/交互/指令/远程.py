"""命令包 Host-for-Client Remote 贡献（对齐上游 `./remote` = typert.remote-client）。

对照 `@Remote`：`list`、`execute`。无 TS 编译器时手写描述符；编解码用严格透传模式。
服务键与命名空间均为 `commands`。
"""
from ..协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

智能体参数={#agent lookup 参数
    'name':'agent',#源码名
    'wire':'agent',#线路字段
    'source':'lookup',#查找
    'lookup':'agent',#lookup 键
    'codec':严格编解码('Agent'),#编解码
}#结束
作用域={'context':'agent','wire':'agent'}#agent scope
包名='@deepseek-ai/dsh-commands'#上游包名
服务='commands'#服务键
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

TYPERT_REMOTE=远程贡献(包名,[列表描述符,执行描述符])#贡献
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default 导出
