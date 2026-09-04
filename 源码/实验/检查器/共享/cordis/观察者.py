"""Host 与 Client 插件面共用的、由生命周期驱动的 Cordis 树发布。

对齐上游 `shared/cordis/observer.ts`。公开面仅中文名。
"""
import threading#微任务调度
from .收集器 import cordis树收集器#树收集器

__all__=['观察cordis树']#仅中文公开名

def 观察cordis树(上下文,监听器,上限):#观察Cordis树
    """观察一个 Cordis 界域并发布不可变的树替换。"""
    收集器=cordis树收集器(上下文.root,上限)#树收集器
    状态={'scheduled':False,'closed':False}#调度状态
    def 发布():#发布一次快照
        """发布一次快照。"""
        状态['scheduled']=False#清排队标记
        if 状态['closed']:#已关闭
            return#跳过
        监听器(收集器.快照())#交给监听器
    def 调度():#合并调度
        """合并调度。"""
        if 状态['scheduled'] or 状态['closed']:#已排或已关
            return#跳过
        状态['scheduled']=True#标记排队
        threading.Thread(target=发布,daemon=True).start()#微任务近似
    清理们=[#事件清理
        上下文.on('internal/plugin',调度,{'global':True}),#插件变更
        上下文.on('internal/status',调度,{'global':True}),#状态变更
    ]#清理列表结束
    发布()#立即发首帧
    def 清理():#清理
        """注销监听器并释放保留对象。"""
        if 状态['closed']:#幂等
            return#已关
        状态['closed']=True#标记关闭
        for 卸 in 清理们:#卸监听
            卸()#调用
        收集器.关闭()#释放收集器
    return 清理#清理函数
