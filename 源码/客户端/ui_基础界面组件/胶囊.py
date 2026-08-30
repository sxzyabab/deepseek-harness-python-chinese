"""小圆角标签芯片。

对齐上游 `ui-primitives/src/Pill.tsx`。公开面仅中文名。
有 onClick 时为可交互按钮；否则为静态 span。
"""

__all__=['胶囊']#仅中文公开名

class 胶囊:#标签芯片
    """结构化视图；宿主渲染真实 DOM。"""
    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构化视图
        """产出胶囊视图模型。"""
        可点=自身.属性.get('onClick') is not None#有点击则交互
        return {#视图
            'type':'pill',#类型
            'tag':'button' if 可点 else 'span',#元素
            'active':bool(自身.属性.get('active')),#选中
            'interactive':可点,#可交互
            'children':自身.属性.get('children'),#子内容
            'onClick':自身.属性.get('onClick'),#点击
            'className':自身.属性.get('className'),#附加类
            'cssModule':'胶囊.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None or 关键字参数:#有新
            合并=dict(属性 or {})#基础
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷新
        return 自身.渲染()#渲染
