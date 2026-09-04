"""由 Host 支撑的已完成 Turn transcript 呈现策略。

对齐上游 `ui-chat/src/client/transcript-view.ts`。公开面仅中文名。
"""
from ..聊天设置 import 默认转录视图模式,转录视图字段#设置常量

__all__=['转录视图策略']#仅中文公开名

class 转录视图策略:#呈现策略
    """Chat 与其设置行消费的实时 transcript 偏好。"""

    def __init__(自身,宿主):#绑定 Host 作用域
        """Host 设置到达前默认为 Compact。"""
        自身._宿主=宿主#设置作用域
        自身._模式=默认转录视图模式#当前模式
        自身._监听们=set()#订阅者
        自身.mode={#响应式当前模式
            'getSnapshot':lambda:自身._模式,#读
            'subscribe':自身._订阅,#订
            'set':自身._设本地,#本地写
        }#mode 结束
        if hasattr(宿主,'subscribe'):#可订
            宿主.subscribe(lambda:自身._采纳())#设置变更时采纳
        自身._采纳()#构造时立即采纳

    def _订阅(自身,监听):#订阅模式
        """返回退订。"""
        自身._监听们.add(监听)#登记
        return lambda:自身._监听们.discard(监听)#退订

    def _通知(自身):#通知订阅者
        """逐个回调。"""
        for 监听 in list(自身._监听们):#拷贝
            监听()#回调

    def _设本地(自身,模式):#仅本地
        """更新快照并通知。"""
        自身._模式=模式#写
        自身._通知()#通知

    def setMode(自身,模式):#写入用户选择
        """发布并持久化一次显式用户选择。"""
        if 自身._模式==模式:#未变
            return#跳过
        自身._设本地(模式)#本地
        设=getattr(自身._宿主,'set',None)#写回
        if callable(设):#有
            设(转录视图字段,模式)#持久化

    def _采纳(自身):#从 Host 拉模式
        """采纳最新已接受的 Host 段，不写回。"""
        快=自身._宿主.getSnapshot() if hasattr(自身._宿主,'getSnapshot') else None#快照
        段=快.get('value') if isinstance(快,dict) else getattr(快,'value',None) if 快 is not None else None#段
        if 段 is None:#缺席
            return#停
        视图=段.get('transcriptView') if isinstance(段,dict) else getattr(段,'transcriptView',None)#模式
        if 视图 is None or 自身._模式==视图:#未变
            return#停
        自身._设本地(视图)#同步
