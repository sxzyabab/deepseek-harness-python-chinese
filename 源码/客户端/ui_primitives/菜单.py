"""锚定下拉菜单。

对齐上游 `ui-primitives/src/Menu.tsx`。公开面仅中文名。
条目含可选行、分隔、标题；可选 portal/子菜单。
"""

__all__=['菜单','是分隔','是标题','视口边距']#仅中文公开名

视口边距=12#portal 边距

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 是分隔(条目):#分隔形
    """type==separator。"""
    return isinstance(条目,dict) and 条目.get('type')=='separator'#分隔

def 是标题(条目):#标题形
    """type==label。"""
    return isinstance(条目,dict) and 条目.get('type')=='label'#标题

class 菜单:#锚定下拉
    """业主控 open；点外/Escape 关。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.开子菜单=None#子菜单 id

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 规范化条目(自身,条目们):#规范化列表
        """产出统一条目视图。"""
        选中=取字段(自身.属性,'selectedId')#单选
        多选=取字段(自身.属性,'selectedIds') or []#多选
        结果=[]#行
        for 条目 in 条目们 or []:#逐条
            if 是分隔(条目):#分隔
                结果.append({'kind':'separator','id':取字段(条目,'id')})#隔
                continue#下
            if 是标题(条目):#标题
                结果.append({'kind':'label','id':取字段(条目,'id'),'text':取字段(条目,'text','')})#标
                continue#下
            标识=取字段(条目,'id')#id
            已选=标识==选中 or 标识 in 多选#选中
            子=取字段(条目,'submenu')#子菜单
            结果.append({#行
                'kind':'item',#项
                'id':标识,#id
                'label':取字段(条目,'label'),#标签
                'disabled':bool(取字段(条目,'disabled',False)),#禁用
                'danger':bool(取字段(条目,'danger',False)),#危险
                'icon':取字段(条目,'icon'),#图标
                'selected':已选,#选中
                'submenu':自身.规范化条目(子) if 子 else None,#子
                'submenuOpen':自身.开子菜单==标识,#子开
            })#行结束
        return 结果#列表

    def 渲染(自身):#结构树
        """锚定+列表。"""
        属性=自身.属性#props
        打开=bool(取字段(属性,'open'))#开
        有子=any(取字段(项,'submenu') for 项 in (取字段(属性,'items') or []) if isinstance(项,dict) and 'submenu' in 项)#有子菜单
        return {#菜单
            'type':'menu',#类型
            'open':打开,#开
            'anchor':取字段(属性,'anchor'),#锚
            'items':自身.规范化条目(取字段(属性,'items')) if 打开 else [],#条目
            'footer':自身.规范化条目(取字段(属性,'footer')) if 打开 else [],#脚
            'align':取字段(属性,'align','start'),#对齐
            'side':取字段(属性,'side','bottom'),#侧
            'portal':bool(取字段(属性,'portal',False)),#portal
            'dense':bool(取字段(属性,'dense',False)),#密
            'compact':bool(取字段(属性,'compact',False)),#紧凑
            'scrollable':打开 and not 有子,#可滚
            'onSelect':取字段(属性,'onSelect'),#选
            'onClose':取字段(属性,'onClose'),#关
            'closeOnPointerLeave':bool(取字段(属性,'closeOnPointerLeave',False)),#离开关
            'getAnchorRect':取字段(属性,'getAnchorRect'),#锚矩形
            'className':取字段(属性,'className'),#类
            'openSubmenu':lambda 标识:自身.__setattr__('开子菜单',标识),#开子
            'cssModule':'菜单.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
