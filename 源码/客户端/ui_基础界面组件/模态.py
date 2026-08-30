"""模态对话框原子。

对齐上游 `ui-primitives/src/Modal.tsx`。公开面仅中文名。
遮罩+居中卡片；Escape/点遮罩关闭；headless 模式无默认页眉。
"""

__all__=['模态','保持毫秒']#仅中文公开名

保持毫秒=0#无自动关闭

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 模态:#全视口对话框
    """受控打开；关则返回 None。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """打开时出遮罩+卡片。"""
        属性=自身.属性#props
        if not bool(取字段(属性,'open')):#关
            return None#不画
        无头=bool(取字段(属性,'headless',False))#无铬
        return {#模态
            'type':'modal',#类型
            'title':取字段(属性,'title',''),#标题/aria
            'closeLabel':取字段(属性,'closeLabel','Close'),#关按钮
            'description':取字段(属性,'description'),#说明
            'children':取字段(属性,'children'),#体
            'footer':取字段(属性,'footer'),#脚
            'className':取字段(属性,'className'),#卡类
            'contentClassName':取字段(属性,'contentClassName'),#内容类
            'headless':无头,#无头
            'onClose':取字段(属性,'onClose'),#关闭
            'cssModule':'模态.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
