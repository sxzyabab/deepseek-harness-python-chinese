'撰写器两排控件放不下一行时，收起模型文字'

__all__=['观察控件行']

def 观察控件行(行):
    '展开后的宽度超过行宽才收起模型文字。返回拆除'
    窗口=行.ownerDocument.defaultView#这一页的窗口，不用全局名
    def 读数(文本):
        'CSS 长度。空和 NaN 当 0'
        数=窗口.parseFloat(文本)
        if 数!=数:
            return 0
        return 数
    def 测量():
        '先按展开量，再决定是否收起'
        行.removeAttribute('data-model-compact')
        样式=窗口.getComputedStyle(行)
        可用=行.getBoundingClientRect().width-读数(样式.paddingLeft)-读数(样式.paddingRight)
        宽度=[]
        子列表=行.children
        下标=0
        while 下标<子列表.length:
            宽=子列表[下标].getBoundingClientRect().width
            if 宽>0:
                宽度.append(宽)
            下标+=1
        需要=sum(宽度)
        if len(宽度)>1:
            间隙=读数(样式.columnGap)
            需要+=max(0,len(宽度)-1)*间隙
        if 需要>可用:
            行.setAttribute('data-model-compact','')
        else:
            行.removeAttribute('data-model-compact')
    测量()
    return lambda:None
