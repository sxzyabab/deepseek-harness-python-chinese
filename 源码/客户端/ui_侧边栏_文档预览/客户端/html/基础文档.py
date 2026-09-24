from html.parser import HTMLParser
from .字节 import 解码文本

__all__=['创建基础超文本文档']

_禁止标签=frozenset({
    'noscript','base','link','meta','iframe','frame','object','embed','set',
    'animate','animatemotion','animatetransform','script',
})
_禁止属性=frozenset({'href','xlink:href'})
_策略="default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:; media-src data:; connect-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'"

class _净化器(HTMLParser):
    """去掉脚本、网络资源、表单与嵌套帧。"""
    def __init__(自身):
        super().__init__(convert_charrefs=True)
        自身.块=[]
        自身.跳过=0

    def handle_starttag(自身,标签,属性表):
        名=标签.lower()
        if 自身.跳过>0 or 名 in _禁止标签:
            if 名 in _禁止标签:
                自身.跳过+=1
            return
        属性=' '.join(
            键+'="'+str(值).replace('"','&quot;')+'"'
            for 键,值 in 属性表
            if 键.lower() not in _禁止属性 and 值 is not None
        )
        自身.块.append('<'+标签+(' '+属性 if 属性 else '')+'>')

    def handle_endtag(自身,标签):
        名=标签.lower()
        if 名 in _禁止标签:
            if 自身.跳过>0:
                自身.跳过-=1
            return
        if 自身.跳过>0:
            return
        自身.块.append('</'+标签+'>')

    def handle_data(自身,数据):
        if 自身.跳过==0:
            自身.块.append(数据.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))

    def handle_startendtag(自身,标签,属性表):
        名=标签.lower()
        if 自身.跳过>0 or 名 in _禁止标签:
            return
        自身.handle_starttag(标签,属性表)

def 创建基础超文本文档(数据):
    """净化后在 head 最前插入限制性 CSP。"""
    清洗=_净化器()
    清洗.feed(解码文本(数据))
    清洗.close()
    正文=''.join(清洗.块)
    元='<meta http-equiv="Content-Security-Policy" content="'+_策略+'">'
    低=正文.lower()
    位=低.find('<head')
    if 位>=0:
        结束=正文.find('>',位)
        正文=正文[:结束+1]+元+正文[结束+1:]
    else:
        正文='<head>'+元+'</head>'+正文
    if not 低.startswith('<!doctype'):
        正文='<!doctype html>'+正文
    return 正文
