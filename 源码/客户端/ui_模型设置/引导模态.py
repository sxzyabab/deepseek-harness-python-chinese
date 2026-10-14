from nicegui import ui as 界面
from .模型分区 import _读样式,挂到根#样式挂到模态根

__all__=['引导模态','忽略隐式关闭']

界面.add_css(挂到根(_读样式('引导模态.module.css'),'引导模态根'),shared=True)

def 忽略隐式关闭():#模态隐式关闭空操作
    '引导步不得被背景点击关掉'
    return#空

class 引导模态:#阻塞引导对话框
    '保持应用根 inert；步骤自有正文与动作'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        '标题 + 正文槽'
        聚焦标题=bool(自身.属性['focusTitle']) if 'focusTitle' in 自身.属性 else False#是否聚焦标题
        标题=自身.属性['title'] if 'title' in 自身.属性 else ''
        子=自身.属性['children'] if 'children' in 自身.属性 else None
        with 界面.dialog() as 对话框:
            with 界面.card().classes('onboarding-modal 引导模态根 dialog'):
                with 界面.column().classes('content'):#正文
                    if 标题!='':
                        标题签=界面.label(标题).classes('title')
                        if 聚焦标题:
                            标题签.props('autofocus')
                    with 界面.column().classes('body'):#子内容
                        if hasattr(子,'渲染'):
                            子.渲染()
                        elif isinstance(子,list):
                            for 项 in 子:
                                if hasattr(项,'渲染'):
                                    项.渲染()
                                elif isinstance(项,str) and 项!='':
                                    界面.label(项)
                        elif isinstance(子,str) and 子!='':
                            界面.label(子)
        对话框.open()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
