from .文案 import 预设展示文案#展示文案

__all__=['预设菜单']#仅中文公开名

class 预设菜单:
    """表面只差文案与样式；菜单行为一致。属性是 dict。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性) if 属性 is not None else {}#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """产出菜单与触发按钮视图。"""
        属性=自身.属性#props
        翻译=属性['t']#翻译
        选项列表=属性['options']#选项
        条目=[]#菜单项
        for 项 in 选项列表:#逐项
            展示=预设展示文案(项,翻译)#展示
            名=展示['name']#名
            信=项['trust'] if 'trust' in 项 else None#信任
            标签=名+' · '+翻译('userTrust') if 信=='user' else 名#标签
            条目.append({'id':项['id'],'label':标签})#项
        打开=属性['open']#开
        改开=属性['onOpenChange']#开闭
        选定=属性['onSelect']#选定
        def 关():
            """关。"""
            改开(False)#关
        def 点选(标识):
            """关再选。"""
            关()#关
            选定(标识)#提交
        def 切换():
            """翻转。"""
            改开(not 打开)#翻转
        return {#视图
            'type':'preset-menu',#类型
            'open':打开,#开
            'onClose':关,#关
            'items':条目,#项
            'selectedId':属性['selectedId'] if 'selectedId' in 属性 else '',#选中
            'onSelect':点选,#选定
            'align':'end',#对齐
            'portal':True,#传送
            'anchor':{#触发
                'type':'button',#按钮
                'className':属性['buttonClassName'] if 'buttonClassName' in 属性 else None,#按钮类
                'chevronClassName':属性['chevronClassName'] if 'chevronClassName' in 属性 else None,#箭头类
                'label':属性['label'] if 'label' in 属性 else '',#标签
                'disabled':属性['disabled'] if 'disabled' in 属性 else False,#禁用
                'expanded':打开,#展开
                'onClick':切换,#点击
            },#触发结束
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有
            合并=dict(属性) if 属性 is not None else {}#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
