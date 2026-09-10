"""文档拥有方累计文本上的一份保留 Markdown 渲染器。

对齐上游 `ui-sidebar-documentpreview/src/client/markdown/MarkdownBody.tsx`。公开面仅中文名。
"""

__all__=['标记文本体']#仅中文公开名


def 标记文本体(内容,翻译):
    """产出 Markdown 结构，或非文本交付时无。"""
    if 内容.get('kind')!='text':#非文本
        return None#无
    return {#结构
        'kind':'markdown-body',
        'text':内容['text'],
        'streaming':not 内容['eof'],
        'labels':{
            'code':{'copyLabel':翻译('code.copy'),'copiedLabel':翻译('code.copied')},
            'footnotes':翻译('footnotes'),
        },
    }#结束
