"""文档级原图预览灯箱。

对齐上游 `ui-attachment/src/ImageLightbox.tsx`。公开面仅中文名。
Escape、遮罩或关闭钮关闭；卸载时恢复焦点。
"""

__all__=['原图灯箱']#仅中文公开名

class 原图灯箱:#原图预览对话框
    """单击缩略图打开的原图预览。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.存活=True#存活

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        """标死。"""
        自身.存活=False#死

    def 关闭(自身):#关闭
        """转调 onClose。"""
        回调=自身.属性['onClose'] if 'onClose' in 自身.属性 else None#回调
        if 回调 is not None:#有
            回调()#关闭

    def 按键(自身,键名):#键盘
        """Escape 关闭。"""
        if 键名=='Escape':#逃逸
            自身.关闭()#关闭

    def 视图(自身):#读视图模型
        """投影对话框。"""
        文案=自身.属性['labels'] if 'labels' in 自身.属性 and 自身.属性['labels'] is not None else {}#文案
        return {#视图
            'src':自身.属性['src'] if 'src' in 自身.属性 else None,#原图 URL
            'alt':自身.属性['alt'] if 'alt' in 自身.属性 else None,#替代文本
            'dialog':文案['dialog'] if 'dialog' in 文案 else None,#对话框名
            'close':文案['close'] if 'close' in 文案 else None,#关闭文案
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
