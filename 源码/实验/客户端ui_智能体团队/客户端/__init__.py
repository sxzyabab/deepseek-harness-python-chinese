"""把生成的 Team Remote 制品绑到其客户端 UI 的浏览器入口。

对齐上游 `client-ui-agent-team/src/client/index.ts`。公开面仅中文名。
"""
from .挂载 import 注入,挂载智能体团队界面,登记界面#挂载
from .团队动作 import 团队动作#UI
from .文案 import 命名空间,中文,英文#词典

__all__=[#仅中文公开名
    '注入','应用','挂载智能体团队界面','团队动作',
    '命名空间','中文','英文',
]#公开面结束

def 应用(上下文,远程制品=None):#浏览器 apply
    """挂载生成的 Team Remote contribution 及其浏览器 UI。"""
    if 远程制品 is None:#无制品则只登记 UI
        return 登记界面(上下文)#仅 UI
    return 挂载智能体团队界面(上下文,远程制品)#挂载 UI 与 Remote

inject=注入#Cordis 别名
apply=应用#入口
