
__all__=['页行','已载入页','末已载行','滚到行']#仅中文公开名


def 页行(页):
    """把已载入页拆成源码行。页为 dict：text / lines。"""
    if 页['lines']==0:#零行
        return []#空
    return 页['text'].split('\n')#行


def 已载入页(页表):
    """按源码位置排序已载入页。页表为 offset → 页 dict。"""
    列表=[{'offset':int(偏移),**页} for 偏移,页 in 页表.items()]#展开
    列表.sort(key=lambda 项:项['offset'])#排序
    return 列表#有序


def 末已载行(页列表):
    """求已载入源码前缀的末行。"""
    if len(页列表)==0:#空
        return 0#零
    末=页列表[-1]#末页
    return 末['offset']+末['lines']-1#末行


def 滚到行(正文,行号):
    """揭示纯文本或高亮源码行。正文须暴露 querySelector / scrollTop。

    代码内容视口带 `data-code-block-content` 时在 `pre .line` 上取行；
    返回当前渲染器是否暴露该行。浏览器 DOM 语义；无 DOM 时返回 False。
    """
    if not hasattr(正文,'querySelector'):#无 DOM
        return False#不可滚
    内代码=hasattr(正文,'hasAttribute') and 正文.hasAttribute('data-code-block-content')#代码内容视口
    纯=正文.querySelector('[data-textpreview-line="'+str(行号)+'"]')#纯文本锚
    代码=None#默认
    if 内代码:#代码视口
        代码节点=正文.querySelectorAll('pre .line')#行集
        代码=代码节点.item(行号-1) if hasattr(代码节点,'item') else None#第 N 行
    行=纯 if 纯 is not None else 代码#锚
    if 行 is None:#无锚
        return False#失败
    正文.scrollTop=max(0,getattr(行,'offsetTop',0))#滚到
    return True#成功
