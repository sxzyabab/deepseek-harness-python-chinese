"""轨迹轮次头：粘性栏，Input/Output/Think/Time 列标签。

对齐上游 `ui-trajectory/src/client/TrajectoryTurnHeader.tsx`。公开面仅中文名。
"""

__all__=['轨迹轮次头','列标签']#仅中文公开名

列标签=('Input','Output','Think','Time')#度量列字面

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 轨迹轮次头:#粘性轮次栏
    """Turn N + 四列度量标签。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """与上游 JSX 同构。"""
        属性=自身.属性#props
        轮次=取字段(属性,'turn')#轮次
        return {#结构树
            'type':'trajectory-turn-header',#类型
            'turn':轮次,#轮次
            'title':'Turn '+str(轮次),#标题
            'columns':list(列标签),#列
            'cssModule':'轨迹轮次头.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
