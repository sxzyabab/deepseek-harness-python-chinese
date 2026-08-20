"""Composer 提交策略：忙碌-Enter 偏好与键盘手势解析。

对齐上游 `ui-conversation/src/client/input/submission-policy.ts`。公开面仅中文名。
真正的投递窗口权威仍在 Host 与 Agent。
"""
from ..提交设置 import 忙碌回车字段,默认忙碌回车行为#字段与默认
from .约定.提交约定 import 默认忙碌回车行为 as 默认行为#再导出别名

__all__=['快照仓库','提交策略','默认忙碌回车行为']#仅中文公开名

默认忙碌回车行为=默认行为#公开默认

class 快照仓库:#简易偏好快照
    """值 + 订阅。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=初值#当前偏好
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读
        """返回当前偏好。"""
        return 自身.状态#值

    def subscribe(自身,回调):#订阅
        """登记。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):#替换
        """写入并通知。"""
        自身.状态=下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 提交策略:#忙碌-Enter 策略
    """composer 注入面与其设置行共用。"""
    def __init__(自身,宿主=None):#可选持久偏好作用域
        """缺席的组合保持进程本地。"""
        自身.busyEnter=快照仓库(默认忙碌回车行为)#实时偏好
        自身.宿主=宿主#可选作用域
        if 宿主 is not None:#有宿主才订阅并立刻采纳
            宿主.subscribe(lambda:自身.采纳(宿主))#作用域发布时再采纳
            自身.采纳(宿主)#构造时先采纳一次

    def resolve(自身,忙碌,手势,可转向):#手势 → 投递模式
        """不改状态。未忙碌或不可转向则一律排队。"""
        if not 忙碌 or not 可转向:#未忙碌或不可转向
            return 'queue'#排队
        偏好=自身.busyEnter.getSnapshot()#当前偏好
        if 手势=='enter':#普通 Enter
            return 偏好#用偏好
        return 'steer' if 偏好=='queue' else 'queue'#加速取对侧

    def setBusyEnter(自身,行为):#改忙碌时普通 Enter 行为
        """实时值在持久写入开始之前先发布。"""
        if 自身.busyEnter.getSnapshot()==行为:#已是
            return#跳过
        自身.busyEnter.set(行为)#先发布
        if 自身.宿主 is not None:#有宿主
            写=getattr(自身.宿主,'set',None)#写回
            if callable(写):#可写
                写(忙碌回车字段,行为)#异步写持久

    def 采纳(自身,宿主):#采纳作用域已接受的持久行为，不回写
        """无段落或已一致则跳过。"""
        快照=宿主.getSnapshot() if hasattr(宿主,'getSnapshot') else {}#作用域快照
        段落=快照.get('value') if isinstance(快照,dict) else None#段落
        if 段落 is None:#无段落
            return#跳过
        行为=段落.get(忙碌回车字段) if isinstance(段落,dict) else getattr(段落,忙碌回车字段,None)#busyEnter
        if 行为 is None or 自身.busyEnter.getSnapshot()==行为:#无或已一致
            return#跳过
        自身.busyEnter.set(行为)#只改实时偏好
