from .文案 import 中文文案

__all__=[
    '代码工具条文案','标记文案','差异块文案','读块文案','检索块文案','网页块文案',
]

def 代码工具条文案():
    '共享代码卡工具条。显示用中文原文'
    return {
        'codeLabel':中文文案('codeBlock.title'),
        'wrapLabel':中文文案('codeBlock.wrap'),
        'unwrapLabel':中文文案('codeBlock.unwrap'),
    }

def 标记文案():
    'Markdown 铬文案'
    return {
        'code':{
            'copyLabel':中文文案('copy'),
            'copiedLabel':中文文案('copied'),
            'toolbarLabels':代码工具条文案(),
        },
        'footnotes':中文文案('markdown.footnotes'),
    }

def 差异块文案():
    'diff 卡铬文案'
    条=代码工具条文案()
    条['copy']=中文文案('copy')
    条['copied']=中文文案('copied')
    条['collapseAria']=中文文案('diff.collapseAria')
    def 展开无障碍(数量):
        '展开其余差异的无障碍名'
        return 中文文案('diff.expandAria',{'count':数量})
    def 展开其余(数量):
        '展开其余差异的可见文案'
        return 中文文案('diff.expandRest',{'count':数量})
    条['expandAria']=展开无障碍
    条['collapse']=中文文案('collapse')
    条['expand']=展开其余
    return 条

def 读块文案():
    '读卡铬文案'
    条=代码工具条文案()
    def 窗口文案(已显示,总计):
        '当前窗口行数'
        return 中文文案('read.window',{'shown':已显示,'total':总计})
    def 展开无障碍(数量):
        '展开其余行的无障碍名'
        return 中文文案('read.expandAria',{'count':数量})
    def 展开其余(数量):
        '展开其余行的可见文案'
        return 中文文案('read.expandRest',{'count':数量})
    条['window']=窗口文案
    条['copy']=中文文案('copy')
    条['copied']=中文文案('copied')
    条['collapseAria']=中文文案('read.collapseAria')
    条['expandAria']=展开无障碍
    条['collapse']=中文文案('collapse')
    条['expand']=展开其余
    return 条

def 检索块文案():
    '搜索卡铬文案'
    def 路径摘要(已显示,总计,截断):
        '路径条数'
        键='search.paths.truncated' if 截断 else 'search.paths'
        return 中文文案(键,{'shown':已显示,'total':总计})
    def 匹配摘要(已显示,总计,文件数,截断):
        '匹配条数'
        键='search.matches.truncated' if 截断 else 'search.matches'
        return 中文文案(键,{'shown':已显示,'total':总计,'files':文件数})
    def 展开无障碍(数量):
        '展开其余结果的无障碍名'
        return 中文文案('search.expandAria',{'count':数量})
    def 展开其余(数量):
        '展开其余结果的可见文案'
        return 中文文案('search.expandRest',{'count':数量})
    return {
        'pathsSummary':路径摘要,
        'matchesSummary':匹配摘要,
        'copy':中文文案('copy'),
        'copied':中文文案('copied'),
        'noResults':中文文案('search.noResults'),
        'collapseAria':中文文案('search.collapseAria'),
        'expandAria':展开无障碍,
        'collapse':中文文案('collapse'),
        'expand':展开其余,
    }

def 网页块文案():
    'web 卡铬文案'
    return {
        'noResults':中文文案('web.noResults'),
        'sourcesTruncated':中文文案('web.sourcesTruncated'),
        'http':中文文案('web.http'),
        'contentTruncated':中文文案('web.contentTruncated'),
        'markdown':标记文案(),
    }
