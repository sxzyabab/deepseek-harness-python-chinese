__all__=['代码工具条文案','标记文案','差异块文案','读块文案','检索块文案','网页块文案']

def 代码工具条文案(翻译):
    """共享代码卡工具条。"""
    return {
        'codeLabel':翻译('codeBlock.title'),
        'wrapLabel':翻译('codeBlock.wrap'),
        'unwrapLabel':翻译('codeBlock.unwrap'),
    }

def 标记文案(翻译):
    """Markdown 铬文案。"""
    return {
        'code':{
            'copyLabel':翻译('copy'),
            'copiedLabel':翻译('copied'),
            'toolbarLabels':代码工具条文案(翻译),
        },
        'footnotes':翻译('markdown.footnotes'),
    }

def 差异块文案(翻译):
    """diff 卡铬文案。"""
    工具条=代码工具条文案(翻译)
    def 展开无障碍(数量):
        return 翻译('diff.expandAria',{'count':数量})
    def 展开其余(数量):
        return 翻译('diff.expandRest',{'count':数量})
    return {
        'codeLabel':工具条['codeLabel'],
        'wrapLabel':工具条['wrapLabel'],
        'unwrapLabel':工具条['unwrapLabel'],
        'copy':翻译('copy'),
        'copied':翻译('copied'),
        'collapseAria':翻译('diff.collapseAria'),
        'expandAria':展开无障碍,
        'collapse':翻译('collapse'),
        'expand':展开其余,
    }

def 读块文案(翻译):
    """读卡铬文案。"""
    工具条=代码工具条文案(翻译)
    def 窗口摘要(已示,总数):
        return 翻译('read.window',{'shown':已示,'total':总数})
    def 展开无障碍(数量):
        return 翻译('read.expandAria',{'count':数量})
    def 展开其余(数量):
        return 翻译('read.expandRest',{'count':数量})
    return {
        'codeLabel':工具条['codeLabel'],
        'wrapLabel':工具条['wrapLabel'],
        'unwrapLabel':工具条['unwrapLabel'],
        'window':窗口摘要,
        'copy':翻译('copy'),
        'copied':翻译('copied'),
        'collapseAria':翻译('read.collapseAria'),
        'expandAria':展开无障碍,
        'collapse':翻译('collapse'),
        'expand':展开其余,
    }

def 检索块文案(翻译):
    """搜索卡铬文案。"""
    def 路径摘要(已示,总数,截断):
        键='search.paths.truncated' if 截断 else 'search.paths'
        return 翻译(键,{'shown':已示,'total':总数})

    def 匹配摘要(已示,总数,文件数,截断):
        键='search.matches.truncated' if 截断 else 'search.matches'
        return 翻译(键,{'shown':已示,'total':总数,'files':文件数})

    def 展开无障碍(数量):
        return 翻译('search.expandAria',{'count':数量})

    def 展开其余(数量):
        return 翻译('search.expandRest',{'count':数量})

    return {
        'pathsSummary':路径摘要,
        'matchesSummary':匹配摘要,
        'copy':翻译('copy'),
        'copied':翻译('copied'),
        'noResults':翻译('search.noResults'),
        'collapseAria':翻译('search.collapseAria'),
        'expandAria':展开无障碍,
        'collapse':翻译('collapse'),
        'expand':展开其余,
    }

def 网页块文案(翻译):
    """web 卡铬文案。"""
    return {
        'noResults':翻译('web.noResults'),
        'sourcesTruncated':翻译('web.sourcesTruncated'),
        'http':翻译('web.http'),
        'contentTruncated':翻译('web.contentTruncated'),
        'markdown':标记文案(翻译),
    }
