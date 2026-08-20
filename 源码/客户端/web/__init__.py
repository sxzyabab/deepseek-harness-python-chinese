"""Web 外壳库入口。

对齐上游 `@deepseek-ai/dsh-client-web`。公开面仅中文名。

上游导出 AppWebEntry / AppRoot / boot 等 React 启动链；React/CSS 半按迁移政策跳过。本宿主面迁入平台模块表与加载器状态仓库（外壳自给自足的无 React 内核）。
"""
from .平台 import 平台模块表#再导出平台模块常量
from .加载器状态 import (#再导出加载器状态面
    光纤状态值,#光纤状态
    状态标签表,#标签
    创建信号,#信号
    创建加载器状态仓库,#仓库
)#再导出结束

__all__=[#仅中文公开名
    '平台模块表',
    '光纤状态值',
    '状态标签表',
    '创建信号',
    '创建加载器状态仓库',
    '外壳伪包标识',
]#公开面结束

外壳伪包标识='@deepseek-ai/dsh-client-app-shell'#宿主图把外壳挂到其下的伪条目 id
