"""经基于句柄的持久化接缝做的一次性冷会话读取。

对齐上游 `session-query/src/cold-read.ts`。公开面仅中文名。
"""
from ...内核.会话 import 中断轮次关闭器#中断末回合内存闭合

__all__=['读冷会话日志']#仅中文公开名


def 读冷会话日志(持久化,会话标识,信号=None):
    """不取所有权、不变更存储地读取一份完整已存会话日志，并追加中断末回合闭合。

    打开读句柄，读取已校验连续日志，关闭句柄，再追加 `中断轮次关闭器`，使写者在回合中崩溃的日志折叠为平衡转录。后端失败原样传播。
    """
    选项=None if 信号 is None else {'signal':信号}#可选取消
    打开=getattr(持久化,'打开',None) or getattr(持久化,'open')#打开面
    句柄=打开(会话标识,'read') if 选项 is None else 打开(会话标识,'read',选项)#读句柄
    try:
        已读=句柄.读(0,None,选项)#读完整日志
    except BaseException:
        try:
            句柄.关闭()#坏句柄上的关闭失败无额外价值
        except BaseException:
            pass#吞关闭失败
        raise#抛出读失败
    句柄.关闭()#正常关闭
    事件列表=list(已读['events']) if 已读.get('events') is not None else []#已存事件
    return {
        'eventState':已读['eventState'] if 'eventState' in 已读 else 'detached',#别名状态
        'header':句柄.header,#读开时固定的头
        'inheritedEventCount':getattr(句柄,'inheritedEventCount',0),#继承数
        'events':事件列表+list(中断轮次关闭器(事件列表)),#已存加闭合
    }#平衡冷日志
