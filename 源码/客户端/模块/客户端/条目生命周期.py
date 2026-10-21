from pywebbridge import undefined as 未定义#页面上的 undefined

__all__=['拆除条目纤程','移除包拥有样式','收成节点']#仅中文公开名


def 收成节点(节点表):
    '页面节点表按长度收成列表。不能 for：越界下标是 undefined，不会停'
    if isinstance(节点表,list):
        return 节点表#已经是列表
    长度=节点表.length#节点数
    if isinstance(长度,int) is not True:
        长度=0#不是数值就当空
    结果=[]#收成
    下标=0#下标
    while 下标<长度:
        结果.append(节点表[下标])#按下标取
        下标=下标+1#前进一步
    return 结果#列表


def 拆除条目纤程(条目):
    '清纤程前先摘掉运行时登记，好让刷新导入新代码'
    纤程=getattr(条目,'fiber',None)#协议名 fiber
    if 纤程 is None:#没有纤程
        return#停
    运行时=getattr(纤程,'runtime',None)#运行时
    if 运行时 is not None:#根上下文的运行时是空
        条目.ctx.registry.delete(运行时.callback)#摘登记，避免被当成用户禁用
    while getattr(纤程,'inertia',None) is not None:#等惯性结束
        纤程.inertia.等待()#等这一轮承诺
    if hasattr(条目,'fiber'):#还有字段
        delattr(条目,'fiber')#清掉


def 移除包拥有样式(标识,文档=None):
    '插件清理落定后摘掉它拥有的 style'
    if 文档 is None or 文档 is 未定义:#没有这次握手的文档
        return#停
    for 元素 in 收成节点(文档.querySelectorAll('style[data-plugin]')):#逐个已打标样式
        if 元素.getAttribute('data-plugin')==标识:#属于这个包
            元素.remove()#摘掉
