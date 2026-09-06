"""由 Host 支撑的已完成 Turn transcript 呈现策略。

对齐上游 `ui-chat/src/client/transcript-view.ts`。公开面仅中文名。
宿主快照为 dict。
"""
from ..聊天设置 import 默认转录视图模式,转录视图字段#设置常量

__all__=['转录视图策略']#仅中文公开名

class 转录视图策略:
    """Chat 与其设置行消费的实时 transcript 偏好。"""

    def __init__(自身,宿主):
        """Host 设置到达前默认为 Compact。"""
        自身._宿主=宿主#设置作用域
        自身._模式=默认转录视图模式#当前模式
        自身._监听集合=set()#订阅者
        def 读当前():
            """读当前模式。"""
            return 自身._模式#模式
        自身.mode={#响应式当前模式
            'getSnapshot':读当前,#读
            'subscribe':自身._订阅,#订
            'set':自身._设本地,#本地写
        }#mode 结束
        def 宿主发布():
            """设置变更时采纳。"""
            自身._采纳()#采纳
        宿主.subscribe(宿主发布)#订阅
        自身._采纳()#构造时立即采纳

    def _订阅(自身,监听):
        """返回退订。"""
        自身._监听集合.add(监听)#登记
        def 退订():
            """取消。"""
            自身._监听集合.discard(监听)#删
        return 退订#退订

    def _通知(自身):
        """逐个回调。"""
        for 监听 in list(自身._监听集合):#拷贝
            监听()#回调

    def _设本地(自身,模式):
        """更新快照并通知。"""
        自身._模式=模式#写
        自身._通知()#通知

    def setMode(自身,模式):
        """发布并持久化一次显式用户选择。"""
        if 自身._模式==模式:#未变
            return#跳过
        自身._设本地(模式)#本地
        自身._宿主.set(转录视图字段,模式)#持久化

    def _采纳(自身):
        """采纳最新已接受的 Host 段，不写回。"""
        快=自身._宿主.getSnapshot()#快照
        段=快['value'] if 快 is not None and 'value' in 快 else None#段
        if 段 is None:#缺席
            return#停
        视图=段['transcriptView'] if 'transcriptView' in 段 else None#模式
        if 视图 is None or 自身._模式==视图:#未变
            return#停
        自身._设本地(视图)#同步
