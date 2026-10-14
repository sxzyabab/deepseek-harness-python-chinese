from nicegui import ui as 界面

__all__=['引导面']#仅中文公开名

class 引导面:#引导接管铬
    '一步内容居中舞台；宿主负责 portal 与 inert'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '画出居中舞台里的步骤内容'
        属性=自身.属性#props
        子=属性['children'] if 'children' in 属性 else None#步骤内容
        def 画子(内容):
            '字符串做标签，组件自己画'
            if 内容 is None:#无
                return
            if isinstance(内容,str):#文案
                界面.label(内容)#标签
                return
            if isinstance(内容,(list,tuple)):#多项
                for 项 in 内容:#逐项
                    画子(项)#递归
                return
            if hasattr(内容,'渲染'):#组件
                内容.渲染()#自画
        with 界面.column().classes('引导面').style('align-items:center;justify-content:center;min-height:100%'):#舞台
            画子(子)#步骤

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
