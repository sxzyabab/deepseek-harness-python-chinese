"""Markdown 实现标签与原语外壳。

对齐上游 `ui-sidebar-documentpreview/src/client/markdown/locales.ts`。公开面仅中文名。
"""

__all__=['中文','英文','标记文本预览键']#仅中文公开名

中文={
    'viewer.label':'Markdown',
    'code.copy':'复制',
    'code.copied':'已复制',
    'footnotes':'脚注',
}

标记文本预览键=tuple(中文.keys())

英文={
    'viewer.label':'Markdown',
    'code.copy':'Copy',
    'code.copied':'Copied',
    'footnotes':'Footnotes',
}
