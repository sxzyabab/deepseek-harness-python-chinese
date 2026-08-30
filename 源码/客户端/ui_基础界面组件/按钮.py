"""令牌样式按钮原子。

对齐上游 `ui-primitives/src/Button.tsx`。公开面仅中文名。
变体映射到 --dsw-alias-button-* 填充族。
"""

__all__=['按钮','变体表','尺寸表']#仅中文公开名

变体表=('primary','ghost','outline','toolbar')#视觉变体
尺寸表=('md','sm')#尺寸

class 按钮:#按钮原子
    """结构化视图；宿主渲染真实 DOM。"""
    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构化视图
        """产出按钮视图模型。"""
        变体=自身.属性.get('variant','ghost')#变体
        尺寸=自身.属性.get('size','md')#尺寸
        if 变体 not in 变体表:#非法
            变体='ghost'#退回
        if 尺寸 not in 尺寸表:#非法
            尺寸='md'#退回
        return {#视图
            'type':'button',#类型
            'variant':变体,#变体
            'size':尺寸,#尺寸
            'icon':自身.属性.get('icon'),#前导图标
            'children':自身.属性.get('children'),#子内容
            'disabled':bool(自身.属性.get('disabled')),#禁用
            'onClick':自身.属性.get('onClick'),#点击
            'className':自身.属性.get('className'),#附加类
            'cssModule':'按钮.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None or 关键字参数:#有新
            合并=dict(属性 or {})#基础
            合并.update(关键字参数)#覆盖
            自身.更新(合并)#刷新
        return 自身.渲染()#渲染
