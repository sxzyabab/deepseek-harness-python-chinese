__all__=['文档标题']


class 文档标题:
    '主列是对话时，把主视图那份会话的标题写进浏览器标题'
    def __init__(自身,属性):
        '记下产品和两份钩子，并写上当前标题'
        自身.属性=属性
        自身.已订=False
        自身.渲染()

    def 更新(自身,属性):
        '换一份 props'
        自身.属性=属性

    def 渲染(自身):
        '有会话标题就写成「标题 — 产品」，否则只用产品名'
        属性=自身.属性
        文档=属性['window'].document
        产品=属性['productTitle']
        def 是对话(信息):
            '活动面板为空就是对话'
            return 信息['activePanelId'] is None
        显示=属性['usePanelInfo'](是对话) is True
        标题=None
        if 显示 is True:
            def 取标题(状态):
                'retainedBy.mainView 大于 0 的第一份会话'
                表=状态['byId']
                当前=None
                for 会话 in 表.values():
                    保留=会话['retainedBy']
                    if 'mainView' in 保留 and 保留['mainView'] is not None:
                        主=保留['mainView']
                    else:
                        主=0
                    if 主>0:
                        当前=会话['id']
                        break
                if 当前 is None or 当前 not in 表:
                    return None
                项=表[当前]
                if 'title' not in 项:
                    return None
                return 项['title']
            标题=属性['useSessions'](取标题)
        if 标题 is None:
            文档.title=产品
        else:
            文档.title=str(标题)+' — '+str(产品)
        if 自身.已订 is not True:
            def 重画():
                '面板或会话变了就改文档标题'
                自身.渲染()
            属性['usePanelInfo']._subscribe(重画)
            属性['useSessions']._subscribe(重画)
            自身.已订=True
        return None

    def 拆除(自身):
        '卸下时恢复产品标题'
        自身.属性['window'].document.title=自身.属性['productTitle']

    def __call__(自身,属性=None):
        '再次绘制'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
