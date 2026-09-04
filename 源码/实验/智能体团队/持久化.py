"""对持久 Team 成员 Session 的短命读句柄访问。

对齐上游 `agent-team/src/persisted.ts`。公开面仅中文名。
"""
from ...内核.智能体循环.辅助 import 解开#等待承诺

__all__=['读持久会话']#仅中文公开名

def 读持久会话(持久化,标识,信号):#读持久会话
    """经短命读句柄读取已存会话的头与完整事件日志，返回前关闭句柄。"""
    句柄=解开(持久化.open(标识,'read',{'signal':信号}))#开读句柄
    try:#读取
        return {#视图
            'header':句柄.header,#会话头
            'inheritedEventCount':句柄.inheritedEventCount,#继承事件数
            'events':解开(句柄.read(0,None,{'signal':信号})),#读全量
        }#视图结束
    finally:#关闭
        解开(句柄.close())#关句柄
