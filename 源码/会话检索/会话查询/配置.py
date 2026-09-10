"""组合会话检索服务的公开配置与带类型失败。对齐上游 `session-query/src/config.ts`。"""
from ...模型后端.llm import 装备错误#Harness错误基类

会话查询读取窗口上限=50#`before`/`after` 原始事件窗口的默认上限
会话查询默认持久检查并发=4#一次批量读取里并发检查持久日志的默认上限
会话查询默认准备会话缓存大小=5#可复用冷准备会话观测默认保留数

class 会话查询错误(装备错误):#会话检索错误
    """带类型的会话检索失败，其 code 是封闭分类中的一员。"""
    def __init__(自身,消息,码,选项=None):#构造检索错误
        装备错误.__init__(自身,消息,码,选项)#交给Harness错误基类

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已取消则抛出 SESSION_QUERY_ABORTED。"""
    if 已中止(信号):#已中止
        raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消
