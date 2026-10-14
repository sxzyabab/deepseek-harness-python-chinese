__all__=['会话面板']#仅中文公开名


from nicegui import ui as 界面
from ..异常 import 页面失败文案,贴出失败

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画


class 会话面板:
    '把 main 席转发给 main.conversation。属性为 dict'

    def __init__(自身,属性=None):
        '记下宿主注入的 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 渲染(自身):
        '画出 main.conversation 槽里的会话。'
        属性=自身.属性#props
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#席位渲染
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('会话面板')#面板
        自身.画面.clear()#清空
        with 自身.画面:#面板
            贴出失败(自身)
            渲染槽('main.conversation',{})#槽内组件自己画
