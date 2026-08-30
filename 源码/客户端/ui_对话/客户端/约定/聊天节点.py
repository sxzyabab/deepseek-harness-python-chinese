"""聊天节点约定：按渲染器 kind 的载荷与工具根判断。



对齐上游 `ui-conversation/src/client/contract/chat-nodes.ts`。公开面仅中文名。

ChatNodeDataMap 由各业务模块声明合并；此处保留空登记表与载荷形别名。

"""



__all__=[#仅中文公开名

    '聊天节点数据表','聊天节点种','助手聊天数据','定稿助手聊天数据','工具聊天数据',

    '手动压缩聊天数据','重试聊天数据','回合尾聊天数据','已结算工具','运行中工具',

]#公开面结束



聊天节点数据表={}#按渲染器 kind 登记载荷；其它模块向此表写入



#聊天节点种：Extract<keyof ChatNodeDataMap, string>

#助手聊天数据：status / turn / step / blocks / time / usage? / finalNode?

#定稿助手聊天数据：助手聊天数据且必有 finalNode

#工具聊天数据：root

#手动压缩聊天数据：command / compaction

#重试聊天数据：attempts / current

#回合尾聊天数据：turn / seq / time / closing / branchUnavailable / ttftMs? / tokensPerSecond?

聊天节点种=str#登记表键收窄为 string 的 kind

助手聊天数据=dict#助手聊天行数据形

定稿助手聊天数据=dict#已定稿助手数据形

工具聊天数据=dict#工具聊天行数据形

手动压缩聊天数据=dict#手动压缩聊天行数据形

重试聊天数据=dict#重试聊天行数据形

回合尾聊天数据=dict#回合尾聊天行数据形



def 已结算工具(块):#工具根是否已结算

    """有 kind 即为已结算的 tool-result。"""

    if isinstance(块,dict):#映射

        return 'kind' in 块#有 kind

    return hasattr(块,'kind')#对象



def 运行中工具(块):#工具根是否仍在运行

    """未结算即运行中。"""

    return not 已结算工具(块)#未结算


