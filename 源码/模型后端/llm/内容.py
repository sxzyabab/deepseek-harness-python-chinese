"""内容块结构辅助。

对齐上游 `llm/src/content.ts`。公开面仅中文名；无英文别名。
"""

__all__=('内容含图片',)#仅中文公开名

def 内容含图片(内容):#内容树是否含图片块
    """有类型的模型内容是否含图片块，并走入嵌套的工具结果内容。"""
    for 块 in 内容:#逐块
        if 块['type']=='image':#本块是图片
            return True#本块是图片
        if 块['type']=='tool-result' and 内容含图片(块['content']):#工具结果里递归含图片
            return True#工具结果里递归含图片
    return False#整棵内容树都没有图片
