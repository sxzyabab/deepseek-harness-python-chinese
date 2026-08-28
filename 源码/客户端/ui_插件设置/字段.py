"""插件配置表单手写控件：值字段与只写密钥字段。

对齐上游 `ui-settings-plugins/src/client/fields.tsx`。公开面仅中文名。
控件只报告键入；写文档只发生在卡片保存。
"""

__all__=['取值字段','值字段','密钥字段','ValueField','SecretField']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 值字段:#暂存值字段
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
        非法=bool(取字段(属性,'invalid'))#非法
        覆盖=bool(取字段(属性,'overridden'))#覆盖
        return {#视图
            'type':'value-field',#类型
            'id':取字段(属性,'id'),#控件 id
            'label':取字段(属性,'label'),#标签
            'text':取字段(属性,'text',''),#草稿文本
            'hint':取字段(属性,'invalidLabel') if 非法 else 取字段(属性,'hint'),#提示或非法文案
            'invalid':非法,#非法
            'overridden':覆盖,#覆盖
            'overriddenLabel':取字段(属性,'overriddenLabel') if 覆盖 else None,#覆盖徽章
            'resetLabel':取字段(属性,'resetLabel') if 覆盖 else None,#复位
            'onReset':取字段(属性,'onReset') if 覆盖 else None,#复位句柄
            'placeholder':取字段(属性,'placeholder',''),#占位
            'numeric':取字段(属性,'numeric') is True,#数字键盘
            'disabled':bool(取字段(属性,'disabled')),#禁用
            'onEdit':取字段(属性,'onEdit'),#编辑
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
        已配=bool(取字段(属性,'configured'))#已配置
        return {#视图
            'type':'secret-field',#类型
            'id':取字段(属性,'id'),#控件 id
            'label':取字段(属性,'label'),#标签
            'text':取字段(属性,'text',''),#草稿
            'hint':取字段(属性,'hint'),#提示
            'configured':已配,#已配
            'stateLabel':取字段(属性,'stateLabel'),#状态徽章
            'disabled':bool(取字段(属性,'disabled')),#禁用
            'onEdit':取字段(属性,'onEdit'),#编辑
            'cssModule':'字段.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

ValueField=值字段#上游名
SecretField=密钥字段#上游名
取值字段=值字段#客户端/出厂卡公开名
