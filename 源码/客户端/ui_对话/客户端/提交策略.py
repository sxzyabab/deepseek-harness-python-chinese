"""Composer 提交策略：忙碌-Enter 偏好与键盘手势解析。

对齐上游 `ui-conversation/src/client/input/submission-policy.ts`。公开面仅中文名。
真正的投递窗口权威仍在 Host 与 Agent。
快照为 dict。
"""
from ..提交设置 import 忙碌回车字段,默认忙碌回车行为#字段与默认
from .约定.提交约定 import 默认忙碌回车行为 as 默认行为#再导出别名

__all__=['解析提交模式','快照存储','提交策略','默认忙碌回车行为']#仅中文公开名

默认忙碌回车行为=默认行为#公开默认

def 解析提交模式(偏好,忙碌,手势,可转向):
    """对照忙碌-Enter 偏好解析一次提交手势。普通 Enter 与主发送共享 enter。"""
    if 忙碌 is not True or 可转向 is not True:#未忙碌或不可转向
        return 'queue'#排队
    if 手势=='enter':#普通 Enter
        return 偏好#用偏好
    return 'steer' if 偏好=='queue' else 'queue'#加速取对侧

class 快照存储:
    """值 + 订阅。"""
    def __init__(自身,初值):
        """记下初值。"""
        自身.状态=初值#当前偏好
        自身.监听者=set()#订阅者

    def getSnapshot(自身):
        """返回当前偏好。"""
        return 自身.状态#值

    def subscribe(自身,回调):
        """登记。"""
        自身.监听者.add(回调)#加入
        def 退订():
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):
        """写入并通知。"""
        自身.状态=下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 提交策略:
    """composer 注入面与其设置行共用；栏读 busyEnter，解析走独立函数。"""
    def __init__(自身,宿主=None):
        """缺席的组合保持进程本地。"""
        自身.busyEnter=快照存储(默认忙碌回车行为)#实时偏好
        自身.宿主=宿主#可选作用域
        if 宿主 is not None:#有宿主才订阅并立刻采纳
            def 宿主发布(钉宿主=宿主):
                """作用域发布时再采纳。"""
                自身.采纳(钉宿主)#采纳
            宿主.subscribe(宿主发布)#订阅
            自身.采纳(宿主)#构造时先采纳一次

    def setBusyEnter(自身,行为):
        """实时值在持久写入开始之前先发布。"""
        if 自身.busyEnter.getSnapshot()==行为:#已是
            return#跳过
        自身.busyEnter.set(行为)#先发布
        if 自身.宿主 is not None:#有宿主
            自身.宿主.set(忙碌回车字段,行为)#写持久

    def 采纳(自身,宿主):
        """无段落或已一致则跳过。"""
        快照=宿主.getSnapshot()#作用域快照
        段落=快照['value'] if 快照 is not None and 'value' in 快照 else None#段落
        if 段落 is None:#无段落
            return#跳过
        行为=段落[忙碌回车字段] if 忙碌回车字段 in 段落 else None#busyEnter
        if 行为 is None or 自身.busyEnter.getSnapshot()==行为:#无或已一致
            return#跳过
        自身.busyEnter.set(行为)#只改实时偏好
