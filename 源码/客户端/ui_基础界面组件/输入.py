"""单行输入原子。

对齐上游 `ui-primitives/src/Input.tsx`。公开面仅中文名。
Composer 文本域不在此；本原子用于搜索框与行内表单。属性为 dict。
"""

__all__=['输入']#仅中文公开名

class 输入:#文本输入
    """可选前导图标的单行输入。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """包装+原生 input 属性透传。"""
        属性=自身.属性#props
        透传={}#透传
        for 键,值 in 属性.items():#扫
            if 键 not in ('icon','className'):#非本层
                透传[键]=值#留
        return {#输入
            'type':'input',#类型
            'icon':属性['icon'] if 'icon' in 属性 else None,#图标
            'className':属性['className'] if 'className' in 属性 else None,#类
            'inputProps':透传,#原生属性
            'cssModule':'输入.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
