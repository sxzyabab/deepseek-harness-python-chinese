"""无 Cordis 依赖的 Markdown 原语本地化文案适配。

对齐上游 `ui-chat/src/client/markdown-labels.ts`。公开面仅中文名。
"""

__all__=['markdown标签']#仅中文公开名

def markdown标签(翻译):#构造 Markdown 标签
    """为一版本地化构造完整 Markdown 饰件文案。"""
    return {#标签表
        'code':{'copyLabel':翻译('copy'),'copiedLabel':翻译('copied')},#代码复制文案
        'footnotes':翻译('markdown.footnotes'),#脚注标题
    }#返回结束
