"""Chat 浏览器半公开面。

对齐上游 `ui-chat/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文,NS,zh,en#词典
from .仓库 import 创建聊天仓库,已存回合过程条目#选中 store
from .转录视图 import 转录视图策略#呈现策略
from .markdown标签 import markdown标签#Markdown 文案
from .应用 import 注入,应用#浏览器安装
from .约定.快照 import 空聊天快照#空快照
from .约定.聊天节点 import 是运行中工具,是已结算工具#工具谓词
from .会话节点 import 登记会话节点#会话节点
from .聊天.登记节点渲染器 import 登记聊天节点渲染器#节点渲染器
from .聊天.聊天视图 import 聊天视图#Chat 视图
from .聊天.统计行 import 统计行#统计
from .聊天.审批命令 import 审批命令#审批卡
from .详情.详情面板 import 详情面板#详情
from .详情.工具节点读取 import 查找工具调用#工具查找
from .设置.转录视图行 import 转录视图行#设置行
from .模型.会话上下文 import 会话上下文#上下文模型

__all__=[#仅中文公开名
    '命名空间','中文','英文','NS','zh','en',
    '创建聊天仓库','已存回合过程条目','转录视图策略','markdown标签',
    '注入','应用','空聊天快照','是运行中工具','是已结算工具',
    '登记会话节点','登记聊天节点渲染器','聊天视图','统计行','审批命令',
    '详情面板','查找工具调用','转录视图行','会话上下文',
]#公开面结束
