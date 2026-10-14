from nicegui import ui as 界面
from ...异常 import 页面失败文案

__all__=['可搜索隐藏']#仅中文公开名

class 可搜索隐藏:#可搜索隐藏席位
    '稳定子树根的隐藏态与揭示回调'

    def __init__(自身,隐藏,揭示):#构造
        '记下隐藏与揭示'
        自身.隐藏=隐藏#是否隐藏
        自身.揭示=揭示#揭示回调
        自身.属性=None#当前 hidden 属性
        自身.根=None#列

    def 同步(自身,焦点在子树内=False):#布局期同步
        '隐藏时焦点仍在子树内则先揭示'
        if 自身.隐藏 and 焦点在子树内:#焦点占用
            自身.揭示()#揭示
            return {'hidden':None,'reason':'focus'}#跳过设属性
        if 自身.隐藏:#可查找隐藏
            自身.属性='until-found'#设
        else:#清除
            自身.属性=None
        return {'hidden':自身.属性}#状态

    def 渲染(自身):#界面
        '画出可隐藏列。调用方接着往列里放子组件。'
        失败=None
        if 自身.根 is not None and getattr(自身.根,'parent_slot',None) is not None:
            try:
                自身.根.clear()
            except Exception as 错误:
                自身.根=None
                失败=页面失败文案(错误)
        if 自身.根 is None:
            自身.根=界面.column().classes('可搜索隐藏')
        if isinstance(失败,str) and 失败!='':
            with 自身.根:
                界面.label(失败)
        if 自身.隐藏 is True:
            自身.根.set_visibility(False)
            return
        自身.根.set_visibility(True)

    def __call__(自身,隐藏=None,揭示=None):#调用形
        '对齐钩子刷新'
        if 隐藏 is not None:
            自身.隐藏=隐藏#刷
        if 揭示 is not None:
            自身.揭示=揭示#刷
        自身.渲染()#画
