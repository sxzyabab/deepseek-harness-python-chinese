"""目标包 Host-for-Client Remote 贡献（对齐上游 `./remote`）。

对照 `@Remote`：`create`、`edit`、`pause`、`resume`、`complete`、`clear`。
implementation 指向中文树宿主方法名；服务键与命名空间均为 `goals`。
"""
from ..协议 import 严格编解码,调用描述符,远程贡献#制品辅助

__all__=['TYPERT_REMOTE','默认','远程贡献对象']#公开面

智能体参数={#agent lookup
    'name':'agent','wire':'agent','source':'lookup','lookup':'agent',
    'codec':严格编解码('Agent'),
}#结束
引用参数={'name':'ref','wire':'ref','source':'json','codec':严格编解码('GoalRef')}#GoalRef
作用域={'context':'agent','wire':'agent'}#agent scope
包名='@deepseek-ai/dsh-goal'#上游包名
服务='goals'#服务键
命名空间='goals'#命名空间
类前=包名+'#GoalService.'#调用 id 前缀

创建描述符=调用描述符(#goals/create
    类前+'remoteExportCreate',服务,命名空间,'create',
    [智能体参数,{'name':'request','wire':'request','source':'json','codec':严格编解码('CreateGoalRequest')}],
    严格编解码('CreateGoalResult'),{'file':'src/index.ts','line':575,'column':3},
    实现='远程创建',作用域=作用域,
)#create

编辑描述符=调用描述符(#goals/edit
    类前+'edit',服务,命名空间,'edit',
    [智能体参数,引用参数,{'name':'request','wire':'request','source':'json','codec':严格编解码('EditGoalRequest')}],
    严格编解码('GoalView'),{'file':'src/index.ts','line':267,'column':3},
    实现='编辑',作用域=作用域,
)#edit

暂停描述符=调用描述符(#goals/pause
    类前+'pause',服务,命名空间,'pause',
    [智能体参数,引用参数],严格编解码('GoalView'),
    {'file':'src/index.ts','line':289,'column':3},实现='暂停',作用域=作用域,
)#pause

恢复描述符=调用描述符(#goals/resume
    类前+'resume',服务,命名空间,'resume',
    [智能体参数,引用参数],严格编解码('GoalView'),
    {'file':'src/index.ts','line':300,'column':3},实现='恢复',作用域=作用域,
)#resume

完成描述符=调用描述符(#goals/complete
    类前+'complete',服务,命名空间,'complete',
    [智能体参数,引用参数],严格编解码('GoalView'),
    {'file':'src/index.ts','line':326,'column':3},实现='完成',作用域=作用域,
)#complete

清除描述符=调用描述符(#goals/clear
    类前+'clear',服务,命名空间,'clear',
    [智能体参数,引用参数],严格编解码('GoalRef'),
    {'file':'src/index.ts','line':366,'column':3},实现='清除',作用域=作用域,
)#clear

TYPERT_REMOTE=远程贡献(包名,[#贡献：create 在源码靠后，挂载序仍按 Remote 导出名常用序
    创建描述符,编辑描述符,暂停描述符,恢复描述符,完成描述符,清除描述符,
])#结束
远程贡献对象=TYPERT_REMOTE#中文别名
默认=TYPERT_REMOTE#default
