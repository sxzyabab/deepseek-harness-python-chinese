"""带不可变顺序与稳定实时按键读取器的增量 Chat 发布。

对齐上游 `ui-chat/src/client/contract/snapshot.ts`。公开面仅中文名。
"""

__all__=[#仅中文公开名
    '空列表','空时间线','空节点源','空过程源','空聊天快照',
    '聊天节点源','聊天节点过程源','聊天节点仓库','回合导航项',
    '聊天回合导航索引','聊天位置节点索引','聊天回合过程呈现','遗留会话切片','聊天快照',
]#公开面结束

空列表=()#空列表常量
空时间线={'turnOrder':空列表,'turns':{}}#空时间线
空节点源={'getSnapshot':lambda:None,'subscribe':lambda *_:(lambda:None)}#空节点源
空过程源={'getSnapshot':lambda:None,'subscribe':lambda *_:(lambda:None)}#空过程源

def 聊天节点源(取快照,订阅):#节点源工厂
    """一个已挂载 Chat 节点座位使用的按键可观察源。"""
    return {'getSnapshot':取快照,'subscribe':订阅}#源

def 聊天节点过程源(取快照,订阅):#过程源工厂
    """围绕一个 Chat 节点的轮次过程呈现的按键可观察源。"""
    return {'getSnapshot':取快照,'subscribe':订阅}#源

def 聊天节点仓库(取,源,过程源,值们):#节点 store 工厂
    """Chat 节点的稳定实时按键读取器。"""
    return {'get':取,'source':源,'processSource':过程源,'values':值们}#仓库

def 回合导航项(回合,锚点键,提示,回复):#导航项工厂
    """投影进紧凑 Chat 导航轨道的一个已加载轮次。"""
    return {'turn':回合,'anchorKey':锚点键,'prompt':提示,'response':回复}#项

def 聊天回合导航索引(项们):#导航索引工厂
    """已加载轮次的稳定实时导航投影。"""
    return {'items':项们}#索引

def 聊天位置节点索引(取回合,取步骤):#位置索引工厂
    """Chat 节点的稳定实时 Location 索引。"""
    return {'getTurn':取回合,'getStep':取步骤}#索引

def 聊天回合过程呈现(回合,规格,回合已关,有外部过程,紧凑正文):#过程呈现工厂
    """为一轮过程推导出的跨节点呈现事实。"""
    return {#呈现
        'turn':回合,'spec':规格,'turnClosed':回合已关,
        'hasExternalProcess':有外部过程,'compactAnswer':紧凑正文,
    }#结束

def 遗留会话切片(节点们,回合时序,回合结束,部分,运行中):#遗留切片工厂
    """支撑 StatsLine 与旧顶层快照字段的兼容投影。"""
    return {#切片
        'nodes':节点们,'turnTimings':回合时序,'turnEnds':回合结束,
        'partial':部分,'runningCalls':运行中,
    }#结束

def 聊天快照(顺序,节点们,位置们,导航,时间线,遗留):#Chat 快照工厂
    """带不可变顺序与稳定实时按键读取器的增量 Chat 发布。"""
    return {#快照
        'order':顺序,'nodes':节点们,'locations':位置们,
        'navigation':导航,'timeline':时间线,'legacy':遗留,
    }#结束

空聊天快照=聊天快照(#空 Chat 快照
    空列表,#空顺序
    聊天节点仓库(#空节点 store
        lambda _键:None,#无节点
        lambda _键:空节点源,#空源
        lambda _键:空过程源,#空过程源
        lambda:空列表,#空值列表
    ),#nodes 结束
    聊天位置节点索引(lambda _回合:空列表,lambda _回合,_步:空列表),#空位置
    聊天回合导航索引(lambda:空列表),#空导航
    空时间线,#空时间线
    遗留会话切片(空列表,{},{},None,空列表),#空遗留
)#EMPTY_CHAT_SNAPSHOT 结束
