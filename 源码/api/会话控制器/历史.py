"""冷会话历史分页与 live 事件源。

对齐上游 `session-controller/src/history.ts`。公开面仅中文名。
"""
from .远程错误与并发 import 远程错误,已中止#远程错误与中止

__all__=['会话历史控制器']#仅中文公开名

默认最大消息数=50#默认页大小

class 会话历史控制器:
    """实现冷安全 history 操作。"""

    def __init__(自身,上下文,晋升):
        """保存晋升回调。"""
        自身._上下文=上下文#Cordis
        自身._晋升=晋升#晋升
        自身._关闭关注者集合=set()#follow 关闭器
        def 拆除历史():
            """拆除 follow。"""
            自身._拆除()#委托
        上下文.副作用(拆除历史,'session-controller.history')#拆除

    def _拆除(自身):
        """关闭全部 follower。"""
        for 关闭 in list(自身._关闭关注者集合):#逐个
            关闭()#关
        自身._关闭关注者集合.clear()#清空

    def page(自身,请求,信号):
        """读一页消息对齐历史。请求为 dict。"""
        if 已中止(信号):#取消
            raise 远程错误('gateway/cancelled','session page was aborted',{})#取消
        raise 远程错误('gateway/internal','session.page is not fully ported in this Python slice yet',{})#阻塞：分页逻辑待完整移植

    def follow(自身,请求,信号):
        """跟随追加事件。请求为 dict。"""
        if 已中止(信号):#取消
            return#空
        raise 远程错误('gateway/internal','session.follow is not fully ported in this Python slice yet',{})#阻塞：follow 逻辑待完整移植
