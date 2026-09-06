"""构建已组装应用的工厂。

对齐上游 `ui-renderer/src/client/app.tsx`。公开面仅中文名。
整棵布局树挂在内置 `root` 槽上。依赖为 dict。
"""
__all__=['构建渲染应用']#仅中文公开名

def 构建渲染应用(依赖):
    """产出应用树的工厂；唯一 ctx 级 root 渲染。"""
    上下文=依赖['ctx']#依赖为 {'ctx': 上下文}
    def 渲根():
        """唯一 ctx 级 root 渲染。"""
        return 上下文.slots.renderSlot('root',{})#渲
    return 渲根#工厂
