'纯文本渲染和文档滚动共用的源行'

__all__=['行们','已载页','最后一行','滚到行']

def 行们(页):
    '拆开一页源行。零行页是空列表，空文本但 lines 为 1 则保留一行'
    if 页['lines']==0:
        return []
    return 页['text'].split('\n')

def 已载页(页表):
    '按源位置排好已加载的页'
    列=[]
    for 偏移,页 in 页表.items():
        列.append({'offset':int(偏移),'text':页['text'],'lines':页['lines']})
    列.sort(key=按偏移)
    return 列

def 按偏移(页):
    '源位置'
    return 页['offset']

def 最后一行(页列):
    '已加载前缀的最后一行。没有则 0'
    if len(页列)==0:
        return 0
    末=页列[-1]
    return 末['offset']+末['lines']-1

def 滚到行(正文,行号):
    '把纯文本或高亮源的这一行露出来。当前渲染器没有这一行则 False'
    是代码=正文.hasAttribute('data-code-block-content')
    纯=正文.querySelector('[data-textpreview-line="'+str(行号)+'"]')
    代码=None
    if 是代码:
        行集=正文.querySelectorAll('pre .line')
        下标=行号-1
        if 下标>=0 and 下标<行集.length:
            代码=行集.item(下标)
    行=纯 if 纯 is not None else 代码
    if 行 is None or not hasattr(行,'offsetTop'):
        return False
    顶=行.offsetTop
    if 顶<0:
        顶=0
    正文.scrollTop=顶
    return True
