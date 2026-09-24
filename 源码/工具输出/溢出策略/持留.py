"""有序头尾持留：文本可切、图像必须整块。"""

def 文本切片(文本,长度,尾部):
    """按码点切一段；尾部为真则取末尾。"""
    if 尾部:
        return 文本[len(文本)-长度:] if 长度<=len(文本) else 文本
    return 文本[:长度]

def 适配文本(文本,预算,尾部,定价):
    """在单调 token 估计下装进预算的最大连续文本端。"""
    低=0
    高=len(文本)
    while 低<高:
        中=(低+高+1)//2
        候选=文本切片(文本,中,尾部)
        if len(候选)==0 or 定价({'type':'text','text':候选})<=预算:
            低=中
        else:
            高=中-1
    return 文本切片(文本,低,尾部)

def 持留内容(内容,预算,定价):
    """持留两端且不移动、不部分持留图像。"""
    头=[]
    尾=[]
    先=0
    后=len(内容)-1
    头字符=0
    剩余=(预算+1)//2
    while 先<=后:
        块=内容[先]
        成本=定价(块)
        if 成本<=剩余:
            头.append(块)
            剩余-=成本
            先+=1
            continue
        if 块['type']=='text':
            文本=适配文本(块['text'],剩余,False,定价)
            头字符=len(文本)
            if len(文本)>0:
                头.append({'type':'text','text':文本})
        break
    剩余=预算//2
    while 后>=先:
        原始=内容[后]
        if 后==先 and 原始['type']=='text':
            块={'type':'text','text':原始['text'][头字符:]}
        else:
            块=原始
        成本=定价(块)
        if 成本<=剩余:
            尾.append(块)
            剩余-=成本
            后-=1
            continue
        if 块['type']=='text':
            文本=适配文本(块['text'],剩余,True,定价)
            if len(文本)>0:
                尾.append({'type':'text','text':文本})
        break
    尾.reverse()
    def 字节(块列表):
        """文本块的 UTF-8 字节合计。"""
        合计=0
        for 块 in 块列表:
            if 块['type']=='text':
                合计+=len(块['text'].encode('utf-8'))
        return 合计
    def 图像数(块列表):
        """图像块个数。"""
        计数=0
        for 块 in 块列表:
            if 块['type']=='image':
                计数+=1
        return 计数
    return {
        'head':头,
        'tail':尾,
        'omittedBytes':字节(内容)-字节(头)-字节(尾),
        'omittedImages':图像数(内容)-图像数(头)-图像数(尾),
    }

__all__=['持留内容']
