"""系统提示词披露行。

对齐上游 `ui-chat/src/client/chat/SystemPromptRow.tsx`。公开面仅中文名。
"""

__all__=['系统提示行']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 系统提示行:#系统提示披露
    """折叠展示完整 system 文本。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#开

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 切换(自身):#开合
        """翻转。"""
        自身.打开=not 自身.打开#翻

    def 渲染(自身):#结构树
        """披露。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        数据=取字段(节点,'data') or 节点#数据
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        文=取字段(数据,'text') or ''#文本
        return {'type':'system-prompt-row','title':翻译('message.systemPrompt'),'summary':文[:80],'open':自身.打开,'body':文 if 自身.打开 else None,'onToggle':自身.切换,'cssModule':'系统提示行.module.css'}#行

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
