"""构建已组装应用的工厂。

对齐上游 `ui-renderer/src/client/app.tsx`。公开面仅中文名。
整棵布局树挂在内置 `root` 槽上。
"""
__all__=['构建渲染应用']#仅中文公开名

def 构建渲染应用(依赖):#应用工厂
    """产出应用树的工厂；唯一 ctx 级 root 渲染。"""
    上下文=依赖['ctx'] if isinstance(依赖,dict) else getattr(依赖,'ctx',依赖)#解出上下文
    return lambda:上下文.slots.renderSlot('root',{})#唯一 ctx 级 root 渲染

buildRenderApp=构建渲染应用#上游名
