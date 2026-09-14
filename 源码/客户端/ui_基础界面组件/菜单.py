
__all__=['菜单','是分隔','是标题','视口边距']#仅中文公开名

视口边距=12#portal 边距

def 是分隔(条目):
    """type==separator。条目为 dict。"""
    return 'type' in 条目 and 条目['type']=='separator'#分隔

def 是标题(条目):
    """type==label。条目为 dict。"""
    return 'type' in 条目 and 条目['type']=='label'#标题

class 菜单:#锚定下拉
    """业主控 open；点外/Escape 关。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.开子菜单=None#子菜单 id

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 开子(自身,标识):
        """打开子菜单。"""
        自身.开子菜单=标识#记下

    def 规范化条目(自身,条目表):
        """产出统一条目视图。"""
        选中=自身.属性['selectedId'] if 'selectedId' in 自身.属性 else None#单选
        多选列=自身.属性['selectedIds'] if 'selectedIds' in 自身.属性 else None#多选
        多选=多选列 if 多选列 is not None else []#空则空表
        列=条目表 if 条目表 is not None else []#空则空表
        结果=[]#行
        for 条目 in 列:#逐条
            if 是分隔(条目) is True:#分隔
                结果.append({'kind':'separator','id':条目['id'] if 'id' in 条目 else None})#隔
                continue#下
            if 是标题(条目) is True:#标题
                结果.append({'kind':'label','id':条目['id'] if 'id' in 条目 else None,'text':条目['text'] if 'text' in 条目 else ''})#标
                continue#下
            标识=条目['id'] if 'id' in 条目 else None#id
            已选=标识==选中 or 标识 in 多选#选中
            子=条目['submenu'] if 'submenu' in 条目 else None#子菜单
            结果.append({#行
                'kind':'item',#项
                'id':标识,#id
                'label':条目['label'] if 'label' in 条目 else None,#标签
                'disabled':条目['disabled'] is True if 'disabled' in 条目 else False,#禁用
                'danger':条目['danger'] is True if 'danger' in 条目 else False,#危险
                'icon':条目['icon'] if 'icon' in 条目 else None,#图标
                'selected':已选,#选中
                'submenu':自身.规范化条目(子) if 子 is not None else None,#子；空表仍规范化（JS 空数组为真）
                'submenuOpen':自身.开子菜单==标识,#子开
            })#行结束
        return 结果#列表

    def 渲染(自身):
        """锚定+列表。"""
        属性=自身.属性#props
        打开=属性['open'] is True if 'open' in 属性 else False#开
        条目列=属性['items'] if 'items' in 属性 else None#条目
        条目列=条目列 if 条目列 is not None else []#空则空表
        有子=False#有子菜单
        for 项 in 条目列:#扫
            if 'submenu' in 项 and 项['submenu'] is not None:#有子
                有子=True#记下
                break#停
        脚列=属性['footer'] if 'footer' in 属性 else None#脚
        return {#菜单
            'type':'menu',#类型
            'open':打开,#开
            'anchor':属性['anchor'] if 'anchor' in 属性 else None,#锚
            'items':自身.规范化条目(条目列) if 打开 is True else [],#条目
            'footer':自身.规范化条目(脚列) if 打开 is True else [],#脚
            'align':属性['align'] if 'align' in 属性 else 'start',#对齐
            'side':属性['side'] if 'side' in 属性 else 'bottom',#侧
            'portal':属性['portal'] is True if 'portal' in 属性 else False,#portal
            'dense':属性['dense'] is True if 'dense' in 属性 else False,#密
            'compact':属性['compact'] is True if 'compact' in 属性 else False,#紧凑
            'scrollable':打开 is True and 有子 is False,#可滚
            'onSelect':属性['onSelect'] if 'onSelect' in 属性 else None,#选
            'onClose':属性['onClose'] if 'onClose' in 属性 else None,#关
            'closeOnPointerLeave':属性['closeOnPointerLeave'] is True if 'closeOnPointerLeave' in 属性 else False,#离开关
            'getAnchorRect':属性['getAnchorRect'] if 'getAnchorRect' in 属性 else None,#锚矩形
            'className':属性['className'] if 'className' in 属性 else None,#类
            'openSubmenu':自身.开子,#开子
            'cssModule':'菜单.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
