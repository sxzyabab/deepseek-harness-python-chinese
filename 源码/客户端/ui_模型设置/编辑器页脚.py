__all__=['编辑器页脚']#仅中文公开名

class 编辑器页脚:#提供方卡片动作行
    """Cancel 只在提交飞行中拒绝输入，从不因只读而拒——只读卡仍须可关。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成

    def 更新(自身,属性):#刷新
        """记下最新 props。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的动作行。"""
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#翻译
        忙=bool(自身.属性['busy']) if 'busy' in 自身.属性 else False#飞行中
        提交禁用=bool(自身.属性['submitDisabled']) if 'submitDisabled' in 自身.属性 else False#提交门控
        提交闲=自身.属性['submitLabel'] if 'submitLabel' in 自身.属性 and 自身.属性['submitLabel'] else 'save'#闲时标签键
        提交忙=自身.属性['submitBusyLabel'] if 'submitBusyLabel' in 自身.属性 and 自身.属性['submitBusyLabel'] else 'saving'#忙时标签键
        取消键=自身.属性['cancelLabel'] if 'cancelLabel' in 自身.属性 and 自身.属性['cancelLabel'] else 'cancel'#取消键
        return {#结构化视图
            'type':'editor-footer',#类型
            'busy':忙,#飞行
            'submitDisabled':提交禁用,#门控
            'cancelLabel':翻译(取消键) if 翻译 is not None else 取消键,#取消文案
            'submitLabel':翻译(提交忙 if 忙 else 提交闲) if 翻译 is not None else (提交忙 if 忙 else 提交闲),#提交文案
            'onCancel':自身.属性['onCancel'] if 'onCancel' in 自身.属性 else None,#取消
            'onSubmit':自身.属性['onSubmit'] if 'onSubmit' in 自身.属性 else None,#提交
        }#视图结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
