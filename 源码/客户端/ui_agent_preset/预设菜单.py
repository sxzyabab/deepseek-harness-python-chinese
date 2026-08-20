"""预设选择菜单：行与芯片共用的触发器+菜单。

对齐上游 `ui-agent-preset/src/client/PresetMenu.tsx`。公开面仅中文名。
"""
from .文案 import 预设展示文案#展示文案

__all__=['预设菜单']#仅中文公开名

def 读(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 预设菜单:#共享预设选择器
    """表面只差文案与样式；菜单行为一致。"""
    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构化视图
        """产出菜单与触发按钮视图。"""
        属性=自身.属性#props
        翻译=读(属性,'t')#翻译
        选项们=读(属性,'options') or []#选项
        条目=[]#菜单项
        for 项 in 选项们:#逐项
            展示=预设展示文案(项,翻译) if 翻译 is not None else None#展示
            名=展示['name'] if 展示 is not None else 读(项,'id','')#名
            信=读(项,'trust')#信任
            标签=f"{名} · {翻译('userTrust')}" if 信=='user' and 翻译 is not None else 名#标签
            条目.append({'id':读(项,'id'),'label':标签})#项
        打开=bool(读(属性,'open'))#开
        改开=读(属性,'onOpenChange')#开闭
        选定=读(属性,'onSelect')#选定
        def 关():#关菜单
            """关。"""
            if 改开 is not None:#有
                改开(False)#关
        def 点选(标识):#选定一项
            """关再选。"""
            关()#关
            if 选定 is not None:#有
                选定(标识)#提交
        def 切换():#切换开闭
            """翻转。"""
            if 改开 is not None:#有
                改开(not 打开)#翻转
        return {#视图
            'type':'preset-menu',#类型
            'open':打开,#开
            'onClose':关,#关
            'items':条目,#项
            'selectedId':读(属性,'selectedId',''),#选中
            'onSelect':点选,#选定
            'align':'end',#对齐
            'portal':True,#传送
            'anchor':{#触发
                'type':'button',#按钮
                'className':读(属性,'buttonClassName'),#按钮类
                'chevronClassName':读(属性,'chevronClassName'),#箭头类
                'label':读(属性,'label',''),#标签
                'disabled':bool(读(属性,'disabled')),#禁用
                'expanded':打开,#展开
                'onClick':切换,#点击
            },#触发结束
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
