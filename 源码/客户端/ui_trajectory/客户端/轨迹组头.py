"""轨迹组头：轮次体内 Message / Step N 行。

对齐上游 `ui-trajectory/src/client/TrajectoryGroupHeader.tsx`。公开面仅中文名。
样式正文落在同目录 轨迹组头.module.css，本模块读成 样式表。
"""
import os#同目录样式路径

__all__=['轨迹组头','样式表','样式文件']#仅中文公开名

_本目录=os.path.dirname(os.path.abspath(__file__))#本包目录
样式文件='轨迹组头.module.css'#上游单文件

def _读样式(文件名):#读真实 CSS
    """从同目录读取样式正文。"""
    路径=os.path.join(_本目录,文件名)#绝对路径
    with open(路径,'r',encoding='utf-8') as 文件:#读文件
        return 文件.read()#全文

样式表=_读样式(样式文件)#完整组头样式

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 轨迹组头:#组头行
    """标题 + 可选次要描述。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """与上游 JSX 同构。"""
        属性=自身.属性#props
        描述=取字段(属性,'description')#描述
        return {#结构树
            'type':'trajectory-group-header',#类型
            'title':取字段(属性,'title'),#标题
            'description':描述 if 描述 is not None and 描述!='' else None,#描述
            'css':样式表,#样式正文
            'cssModule':样式文件,#样式文件名
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
