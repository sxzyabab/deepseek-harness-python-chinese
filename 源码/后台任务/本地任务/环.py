"""一份任务背后的有界输出环：绝对字节偏移上的分块、从不移动已赋值偏移的头部淘汰，以及从任意偏移的非消费读取。"""

def utf8尾(文本,最大字节):
    """文本按 UTF-8 计不超过最大字节的尾部；切点落在字符边界。"""
    原始=文本.encode('utf-8')
    起点=len(原始)-最大字节
    if 起点<0:
        起点=0
    while 起点<len(原始) and (原始[起点]&0xC0)==0x80:
        起点+=1
    尾=原始[起点:]
    return {'text':尾.decode('utf-8'),'bytes':len(尾)}

class 输出环:
    """偏移在淘汰后仍绝对：earliest 只前进。"""
    def __init__(自身):
        """建空环。"""
        自身.分块列表=[]
        自身.保留字节=0
        自身.总量=0
        自身.最早=0

    def 追加(自身,文本,选项,上限):
        """追加一块并按上限修剪头部。空块返回假。"""
        if len(文本)==0:
            return False
        字节=len(文本.encode('utf-8'))
        项={'at':自身.总量,'text':文本,'bytes':字节}
        if 选项 is not None and 'channel' in 选项 and 选项['channel'] is not None:
            项['channel']=选项['channel']
        if 选项 is not None and 'gapBefore' in 选项 and 选项['gapBefore'] is not None:
            项['gapBefore']=选项['gapBefore']
        自身.分块列表.append(项)
        自身.总量+=字节
        自身.保留字节+=字节
        自身.修剪(上限)
        return True

    def 修剪(自身,上限):
        """丢掉头部直到环适合上限；单块过大则只留 UTF-8 安全尾并标 gapBefore。"""
        while 自身.保留字节>上限 and len(自身.分块列表)>1:
            丢掉=自身.分块列表.pop(0)
            自身.保留字节-=丢掉['bytes']
        单独=自身.分块列表[0] if len(自身.分块列表)==1 else None
        if 单独 is not None and 单独['bytes']>上限:
            尾=utf8尾(单独['text'],上限)
            单独['at']+=单独['bytes']-尾['bytes']
            单独['text']=尾['text']
            单独['bytes']=尾['bytes']
            单独['gapBefore']=True
            自身.保留字节=尾['bytes']
        自身.最早=自身.分块列表[0]['at'] if len(自身.分块列表)>0 else 自身.总量

    def 从偏移读取(自身,起点):
        """与 [from, total) 相交的保留分块，作为新鲜线路分块。"""
        块列表=[]
        for 块 in 自身.分块列表:
            if 块['at']+块['bytes']<=起点:
                continue
            项={'at':块['at'],'text':块['text']}
            if 'channel' in 块:
                项['channel']=块['channel']
            if 'gapBefore' in 块:
                项['gapBefore']=块['gapBefore']
            块列表.append(项)
        return {'chunks':块列表,'next':自身.总量,'lossy':起点<自身.最早}

__all__=['输出环','utf8尾']
