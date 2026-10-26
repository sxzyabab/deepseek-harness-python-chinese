'显式 Markdown 引用行的识别和解码'
import re

__all__=['引用文本','消息引用区间']

换行=re.compile(r'\r\n?')
标记=re.compile(r'^ {0,3}>[ \t]?',re.MULTILINE)
区间=re.compile(r'^ {0,3}>[^\r\n]*(?:\r?\n {0,3}>[^\r\n]*)*',re.MULTILINE)


def 引用文本(文本):
    '每一行去掉一个引用标记。换行收成换行符'
    return 标记.sub('',换行.sub('\n',文本))


def 消息引用区间(文本):
    '连续的显式引用行。行内大于号仍是普通文字'
    结果=[]
    for 匹配 in 区间.finditer(文本):
        if 引用文本(匹配.group(0)).strip()=='':
            continue
        结果.append({'start':匹配.start(),'end':匹配.end()})
    return 结果
