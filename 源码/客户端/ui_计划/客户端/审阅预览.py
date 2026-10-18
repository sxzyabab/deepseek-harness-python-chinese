import re

__all__=['是否审阅预览地址']

审阅地址模式=re.compile(r'^dsh-resource://plan-review/[^/?#]+/[^/?#]+$')


def 是否审阅预览地址(地址):
    '是不是临时审阅预览。这种地址不进已记录历史'
    return 审阅地址模式.match(地址) is not None
