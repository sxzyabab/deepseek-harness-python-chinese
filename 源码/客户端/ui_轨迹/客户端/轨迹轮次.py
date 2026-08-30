"""轨迹轮次：粘性轮次头 + 正文。

对齐上游 `TrajectoryTurn.tsx` / `TrajectoryTurnHeader.tsx`。公开面仅中文名。
样式正文落在同目录 轨迹轮次.module.css / 轨迹轮次头.module.css。
"""
import os#同目录样式路径

__all__=['轨迹轮次','轨迹轮次头','列标签','轮次样式表','轮次头样式表','轮次样式文件','轮次头样式文件']#仅中文公开名

_本目录=os.path.dirname(os.path.abspath(__file__))#本包目录
轮次样式文件='轨迹轮次.module.css'#轮次正文
轮次头样式文件='轨迹轮次头.module.css'#粘性头

def _读样式(文件名):#读真实 CSS
    """从同目录读取样式正文。"""
    路径=os.path.join(_本目录,文件名)#绝对路径
    with open(路径,'r',encoding='utf-8') as 文件:#读文件
        return 文件.read()#全文

轮次样式表=_读样式(轮次样式文件)#轮次样式
轮次头样式表=_读样式(轮次头样式文件)#轮次头样式

列标签=('Input','Output','Think','Time')#列标签

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 轨迹轮次头:#粘性轮次头
    """Turn N + Input/Output/Think/Time。"""

    def __init__(自身,轮次=1):#1 基轮次
        """记下轮次。"""
        自身.轮次=轮次#轮次

    def 渲染(自身):#结构树
        """产出轮次头。"""
        return {#结构树
            'type':'trajectory-turn-header',#类型
            'title':f'Turn {自身.轮次}',#标题
            'columns':list(列标签),#列
            'css':轮次头样式表,#样式
            'cssModule':轮次头样式文件,#样式文件名
        }#结束

class 轨迹轮次:#一轮
    """粘性头 + 正文子节点。"""

    def __init__(自身,属性=None):#可选 props
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """产出轮次段。"""
        轮=取字段(自身.属性,'turn',1)#轮次
        return {#结构树
            'type':'trajectory-turn',#类型
            'turn':轮,#轮
            'header':轨迹轮次头(轮).渲染(),#头
            'children':取字段(自身.属性,'children'),#子
            'css':轮次样式表,#样式
            'cssModule':轮次样式文件,#样式文件名
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲
