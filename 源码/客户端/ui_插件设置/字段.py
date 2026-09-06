"""插件配置表单手写控件：值字段与只写密钥字段。

对齐上游 `ui-settings-plugins/src/client/fields.tsx`。公开面仅中文名。
控件只报告键入；写文档只发生在卡片保存。
"""

__all__=['取值字段','密钥字段']#仅中文公开名

class 取值字段:#暂存值字段
    """numeric 仅提示键盘；是否合法由规格判定，控件不改写键入。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """标签、覆盖徽章、输入与提示。"""
        属性=自身.属性#props
        非法=bool(属性['invalid']) if 'invalid' in 属性 else False#非法
        覆盖=bool(属性['overridden']) if 'overridden' in 属性 else False#覆盖
        return {#视图
            'type':'value-field',#类型
            'id':属性['id'] if 'id' in 属性 else None,#控件 id
            'label':属性['label'] if 'label' in 属性 else None,#标签
            'text':属性['text'] if 'text' in 属性 else '',#草稿文本
            'hint':属性['invalidLabel'] if 非法 and 'invalidLabel' in 属性 else (属性['hint'] if 'hint' in 属性 else None),#提示或非法文案
            'invalid':非法,#非法
            'overridden':覆盖,#覆盖
            'overriddenLabel':属性['overriddenLabel'] if 覆盖 and 'overriddenLabel' in 属性 else None,#覆盖徽章
            'resetLabel':属性['resetLabel'] if 覆盖 and 'resetLabel' in 属性 else None,#复位
            'onReset':属性['onReset'] if 覆盖 and 'onReset' in 属性 else None,#复位句柄
            'placeholder':属性['placeholder'] if 'placeholder' in 属性 else '',#占位
            'numeric':'numeric' in 属性 and 属性['numeric'] is True,#数字键盘
            'disabled':bool(属性['disabled']) if 'disabled' in 属性 else False,#禁用
            'onEdit':属性['onEdit'] if 'onEdit' in 属性 else None,#编辑
            'cssModule':'字段.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 密钥字段:#只写凭证控件
    """响应从不带回值；空白草稿不写，保留已存密钥。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """标签、已配徽章、密码输入与提示。"""
        属性=自身.属性#props
        已配=bool(属性['configured']) if 'configured' in 属性 else False#已配置
        return {#视图
            'type':'secret-field',#类型
            'id':属性['id'] if 'id' in 属性 else None,#控件 id
            'label':属性['label'] if 'label' in 属性 else None,#标签
            'text':属性['text'] if 'text' in 属性 else '',#草稿
            'hint':属性['hint'] if 'hint' in 属性 else None,#提示
            'configured':已配,#已配
            'stateLabel':属性['stateLabel'] if 'stateLabel' in 属性 else None,#状态徽章
            'disabled':bool(属性['disabled']) if 'disabled' in 属性 else False,#禁用
            'onEdit':属性['onEdit'] if 'onEdit' in 属性 else None,#编辑
            'cssModule':'字段.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
