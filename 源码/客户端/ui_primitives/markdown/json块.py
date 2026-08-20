"""可折叠 JSON 块（会话侧，独立于 RPC 面板 PayloadJson）。

对齐上游 `ui-primitives/src/markdown/JsonBlock.tsx`。公开面仅中文名。
"""
import json#美化

__all__=['json块','最大字符','默认截断标签']#仅中文公开名

最大字符=20000#字符封顶

def 默认截断标签(总计):#脚注
    """超出封顶时的脚。"""
    return '… 已截断，共 '+str(总计)+' 字符'#文案

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class json块:#可折叠 JSON
    """打开时 stringify；超封顶截断。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已打开=bool(取字段(自身.属性,'defaultOpen',False))#默认开

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 切换(自身):#翻转
        """开合。"""
        自身.已打开=not 自身.已打开#翻

    def 渲染(自身):#结构树
        """产出 toggle+可选 body。"""
        属性=自身.属性#props
        截断标=取字段(属性,'truncatedLabel',默认截断标签)#脚格式
        体=''#体
        if 自身.已打开:#开
            载荷=取字段(属性,'payload')#载荷
            try:#stringify
                串=json.dumps(载荷,ensure_ascii=False,indent=2)#美化
                if 串 is None:#不可序列
                    串=str(载荷)#回退
            except Exception:#失败
                串=str(载荷)#回退
            if len(串)>最大字符:#超
                脚=截断标(len(串)) if callable(截断标) else 默认截断标签(len(串))#脚
                体=串[:最大字符]+'\n'+脚#截
            else:#全
                体=串#全
        return {#视图
            'type':'json-block',#类型
            'label':取字段(属性,'label') or '',#标签
            'open':自身.已打开,#开
            'body':体,#体
            'onToggle':自身.切换,#切换
            'cssModule':'json块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
