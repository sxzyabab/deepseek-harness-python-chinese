"""提供方卡片共用的动作行：左取消、右提交。

对齐上游 `ui-settings-models/src/client/EditorFooter.tsx`。公开面仅中文名。
两张卡提交的东西不同，但行本身不关心——只渲染交给它的标签与门控。
"""

__all__=['编辑器页脚']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

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
        翻译=取字段(自身.属性,'t')#翻译
        忙=bool(取字段(自身.属性,'busy'))#飞行中
        提交禁用=bool(取字段(自身.属性,'submitDisabled'))#提交门控
        提交闲=取字段(自身.属性,'submitLabel') or 'save'#闲时标签键
        提交忙=取字段(自身.属性,'submitBusyLabel') or 'saving'#忙时标签键
        取消键=取字段(自身.属性,'cancelLabel') or 'cancel'#取消键
        return {#结构化视图
            'type':'editor-footer',#类型
            'busy':忙,#飞行
            'submitDisabled':提交禁用,#门控
            'cancelLabel':翻译(取消键) if 翻译 else 取消键,#取消文案
            'submitLabel':翻译(提交忙 if 忙 else 提交闲) if 翻译 else (提交忙 if 忙 else 提交闲),#提交文案
            'onCancel':取字段(自身.属性,'onCancel'),#取消
            'onSubmit':取字段(自身.属性,'onSubmit'),#提交
        }#视图结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
