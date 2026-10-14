from nicegui import ui as 界面
from .异常 import 页面失败文案
from .文案 import 预设展示文案#展示文案

__all__=['预设菜单']#仅中文公开名

class 预设菜单:
    '表面只差文案与样式；菜单行为一致。只接收合并后的属性字典。父组件负责调用渲染'
    def __init__(自身,属性=None):
        '只记下属性。父组件会再调用渲染，构造时不画'
        自身.属性=属性 if isinstance(属性,dict) else {}#合并后的属性
        自身.画面=None#可反复清空的容器
        自身.画面失败=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 渲染(自身):
        '画出触发按钮、下拉项和说明'
        属性=自身.属性#props
        if 't' not in 属性 or 'options' not in 属性:#父组件尚未填齐
            return None#不画
        翻译=属性['t']#翻译
        选项列表=属性['options'] if 属性['options'] is not None else []#选项
        条目=[]#菜单项
        for 项 in 选项列表:#逐项
            展示=预设展示文案(项,翻译)#展示
            名=展示['name']#名
            信=项['trust'] if 'trust' in 项 else None#信任
            标签=名+' · '+翻译('userTrust') if 信=='user' else 名#标签
            行={'id':项['id'],'label':标签}#项
            述=展示['description'] if 'description' in 展示 else None#说明
            if 述 is None:#无述
                述=翻译('noDescription')#回退
            if 述 is not None:#有说明
                行['description']=述#说明
            条目.append(行)#项
        改开=属性['onOpenChange'] if 'onOpenChange' in 属性 else None#开闭
        选定=属性['onSelect'] if 'onSelect' in 属性 else None#选定
        打开='open' in 属性 and 属性['open'] is True#显式打开
        def 关():
            '关'
            if 改开 is not None:
                改开(False)#关
        def 点选(标识):
            '关再选'
            关()#关
            if 选定 is not None:
                选定(标识)#提交
        def 切换():
            '翻转'
            if 改开 is not None:
                改开(not 打开)#翻转
        标签=属性['label'] if 'label' in 属性 else ''#按钮文
        选中=属性['selectedId'] if 'selectedId' in 属性 else ''#当前
        禁用='disabled' in 属性 and 属性['disabled'] is True#显式禁用
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column()#根
        自身.画面.clear()#再清一次
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            钮=界面.button(标签, on_click=切换)#触发
            钮类=属性['buttonClassName'] if 'buttonClassName' in 属性 else None#父组件给定的按钮类
            if isinstance(钮类,str) and 钮类!='':
                钮.classes(钮类)#挂上选择器样式
            if 禁用:#禁用
                钮.disable()#禁
            with 钮:#菜单挂在按钮上
                with 界面.menu() as 菜单:#菜单
                    for 项 in 条目:#逐项
                        def 点此项(标识=项['id']):
                            '选定该项'
                            点选(标识)#提交
                        with 界面.column():#名称与说明
                            菜单项=界面.menu_item(项['label'], on_click=点此项)#项
                            if 项['id']==选中:#当前
                                菜单项.classes(add='selected')#选中
                            if 'description' in 项:#说明单独成行
                                界面.label(项['description'])#说明
            if 打开:#父组件要求打开
                菜单.open()#打开

    def __call__(自身,属性=None):
        '只接收一个属性字典'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
