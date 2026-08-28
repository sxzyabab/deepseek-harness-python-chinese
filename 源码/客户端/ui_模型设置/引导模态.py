"""产品引导步骤共用的阻塞模态外壳。

对齐上游 `ui-settings-models/src/client/OnboardingModal.tsx`。公开面仅中文名。
"""

__all__=['引导模态','OnboardingModal','忽略隐式关闭']#仅中文公开名

def 忽略隐式关闭():#模态隐式关闭空操作
    """引导步不得被背景点击关掉。"""
    return#空

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

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
        聚焦标题=bool(取字段(自身.属性,'focusTitle',False))#是否聚焦标题
        return {#视图
            'type':'onboarding-modal',#类型
            'open':True,#始终打开
            'title':取字段(自身.属性,'title',''),#标题
            'focusTitle':聚焦标题,#聚焦标题
            'onClose':忽略隐式关闭,#拒绝隐式关闭
            'children':取字段(自身.属性,'children'),#正文
            'cssModule':'引导模态.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

OnboardingModal=引导模态#上游名
