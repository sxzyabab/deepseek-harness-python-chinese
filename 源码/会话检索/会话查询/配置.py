'组合会话检索服务的公开配置与带类型失败'
from .异常 import 会话查询错误#检索错误
from ...基础设施.通用工具 import 已中止

会话查询读取窗口上限=50#`before`/`after` 原始事件窗口的默认上限
会话查询默认持久检查并发=4#一次批量读取里并发检查持久日志的默认上限
会话查询默认准备会话缓存大小=5#可复用冷准备会话观测默认保留数

def 若已中止则抛出(信号):
    '已取消则抛出 SESSION_QUERY_ABORTED'
    if 已中止(信号):#已中止
        raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消
