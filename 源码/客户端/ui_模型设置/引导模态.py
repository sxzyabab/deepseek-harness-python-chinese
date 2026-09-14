__all__=['引导模态','忽略隐式关闭']#仅中文公开名

def 忽略隐式关闭():#模态隐式关闭空操作
    """引导步不得被背景点击关掉。"""
    return#空

class 引导模态:#阻塞引导对话框
    """保持应用根 inert；步骤自有正文与动作。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """标题 + 正文槽。"""
        聚焦标题=bool(自身.属性['focusTitle']) if 'focusTitle' in 自身.属性 else False#是否聚焦标题
        return {#视图
            'type':'onboarding-modal',#类型
            'open':True,#始终打开
            'title':自身.属性['title'] if 'title' in 自身.属性 else '',#标题
            'focusTitle':聚焦标题,#聚焦标题
            'onClose':忽略隐式关闭,#拒绝隐式关闭
            'children':自身.属性['children'] if 'children' in 自身.属性 else None,#正文
            'cssModule':'引导模态.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
