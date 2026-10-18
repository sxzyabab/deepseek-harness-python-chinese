'空白候选和引用候选共用游标、优先级和事实缓存'

__all__=['折叠空白规则','修剪空白规则']

def 替换(文本,起,止,显示):
    '一段原文配上只用于显示的文字'
    return {'id':'text','start':起,'end':止,'data':{'text':文本[起:止],'display':显示}}

def 匹配折叠(文本,从,上下文):
    '下一处会收成一个空格的空白。单个空格和已在空白里的游标跳过'
    if not 上下文['read']('collapseWhitespace'):
        return None
    import re
    空白=re.compile(r'\s+')
    匹配=空白.search(文本,从)
    while 匹配 is not None:
        起点=匹配.start()
        if (起点>0 and 文本[起点-1].isspace()) or 匹配.group(0)==' ':
            匹配=空白.search(文本,匹配.end())
            continue
        return 替换(文本,起点,起点+len(匹配.group(0)),' ')
    return None

def 匹配修剪(文本,从,上下文):
    '文档两端的空白。同一起点时比折叠更优先'
    if not 上下文['read']('trimWhitespace'):
        return None
    if 从==0:
        import re
        前导=re.match(r'^\s+',文本)
        if 前导 is not None:
            return 替换(文本,0,len(前导.group(0)),'')
    起点=len(文本)
    while 起点>0 and 文本[起点-1].isspace():
        起点-=1
    if 起点==len(文本) or 起点<从:
        return None
    return 替换(文本,起点,len(文本),'')

折叠空白规则={
    'id':'text.collapse-whitespace',
    'order':1010,
    'match':匹配折叠,
}
修剪空白规则={
    'id':'text.trim-whitespace',
    'order':1000,
    'match':匹配修剪,
}
