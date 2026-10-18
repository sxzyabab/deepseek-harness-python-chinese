from ...异常 import 挂上

__all__=['会话面板']

class 会话面板:
    '主栏里的会话占位。会话绑定属于它的子槽'
    def __init__(自身,属性):
        '画出 main.conversation'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '把已登记的会话根放进这一格'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        elif 'parent' in 属性:
            父=属性['parent']
        壳=文档.createElement('div')
        壳.style.display='contents'
        挂上(壳,属性['renderSlot']('main.conversation',{'window':窗口}))
        自身.根=壳
        if 父 is not None:
            父.appendChild(自身.根)
        return 自身.根
