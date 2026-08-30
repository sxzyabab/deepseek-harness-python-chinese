"""槽位宿主与已安装渲染器之间的无 React 约定。

对齐上游 `ui-slots/src/renderer.ts`。公开面仅中文名。React 渲染器实现按迁移政策跳过；本模块迁入错误类型与宿主面名词。
"""

__all__=['过期授权错误','槽位所有权错误']#仅中文公开名

class 过期授权错误(Exception):#声明条目拆除后仍调用保留的 renderSlot 绑定
    """保留的 renderSlot 绑定在其声明条目拆除后仍被调用时抛出。"""
    pass#无额外字段

class 槽位所有权错误(Exception):#对 children 声明之外的键调用 renderSlot 绑定时抛出
    """对条目 children 声明之外的键调用 renderSlot 绑定时抛出。"""
    pass#无额外字段
