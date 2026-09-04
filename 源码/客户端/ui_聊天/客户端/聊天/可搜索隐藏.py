"""施加可搜索隐藏状态，且不卸载稳定子树。

对齐上游 `ui-chat/src/client/chat/searchable-hidden.ts`。公开面仅中文名。
无真 DOM：以结构描述 hidden/until-found 与 beforematch 揭示。
"""

__all__=['可搜索隐藏']#仅中文公开名

class 可搜索隐藏:#可搜索隐藏席位
    """稳定子树根的隐藏态与揭示回调。"""

    def __init__(自身,隐藏,揭示):#构造
        """记下隐藏与揭示。"""
        自身.隐藏=隐藏#是否隐藏
        自身.揭示=揭示#揭示回调
        自身.属性=None#当前 hidden 属性

    def 同步(自身,焦点在子树内=False):#布局期同步
        """隐藏时焦点仍在子树内则先揭示。"""
        if 自身.隐藏 and 焦点在子树内:#焦点占用
            自身.揭示()#揭示
            return {'hidden':None,'reason':'focus'}#跳过设属性
        if 自身.隐藏:#可查找隐藏
            自身.属性='until-found'#设
        else:#清除
            自身.属性=None#清
        return {'hidden':自身.属性}#状态

    def 渲染(自身):#结构树
        """返回隐藏描述。"""
        return {'type':'searchable-hidden','hidden':自身.属性,'cssHint':'until-found'}#视图

    def __call__(自身,隐藏=None,揭示=None):#调用形
        """对齐钩子刷新。"""
        if 隐藏 is not None:#有
            自身.隐藏=隐藏#刷
        if 揭示 is not None:#有
            自身.揭示=揭示#刷
        return 自身.渲染()#渲
