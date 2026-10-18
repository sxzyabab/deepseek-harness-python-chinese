from .markdown.Markdown文本 import 处理Markdown文本

__all__=['网页块','处理网页块','安全链接','链接标签']#仅中文公开名

样式表='''
.网页块{margin:16px 0;padding:12px 14px;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-markdown-code-block);border-radius:var(--dsw-radius-lg);display:flex;flex-direction:column}
.网页块 a{color:var(--dsw-alias-link);font-weight:500;text-decoration:none}
.网页块 a:hover{text-decoration:underline dotted;text-underline-offset:3px}
'''

def 安全链接(网址):
    '仅 http(s)；否则 None 走纯文本'
    if isinstance(网址,str) is False or 网址=='':#空
        return None#无
    低=网址.lower()#小写
    if 低.startswith('http://') or 低.startswith('https://'):#协议
        if '://' not in 网址:#畸形
            return None#无
        return 网址#可用
    return None#非 http

def 链接标签(网址,标题):
    '有标题用标题；否则主机名；再否则原文'
    if isinstance(标题,str) and 标题!='':
        return 标题#标题
    余=网址.split('://',1)[-1]#去协议
    主机=余.split('/',1)[0].split('?',1)[0].split('#',1)[0]#主机
    return 主机 if 主机!='' else 网址#主机或原文

def 处理网页块(window,属性):
    '按 kind 画出抓取链接或检索来源。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('网页块样式') is None:
        样式=文档.createElement('style')
        样式.id='网页块样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    种=属性['kind'] if 'kind' in 属性 else None#种
    类名=属性['className'] if 'className' in 属性 else None#类
    根=文档.createElement('div')
    根.className='网页块'
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    def 挂链(父,文,址):
        '可链则 a，否则纯文本'
        if 址 is not None:
            链=文档.createElement('a')
            链.href=址
            链.target='_blank'
            链.textContent=文
            父.appendChild(链)
        elif 文!='':
            标=文档.createElement('div')
            标.textContent=文
            父.appendChild(标)
    if 种=='fetch':#抓取
        网址=属性['url'] if 'url' in 属性 and 属性['url'] is not None else ''#url
        挂链(根,网址,安全链接(网址))
        码=属性['statusCode'] if 'statusCode' in 属性 else None#状态码
        if 码 is not None:
            状态=文档.createElement('div')
            状态.textContent=str(码)
            根.appendChild(状态)
    else:
        答案=属性['answer'] if 'answer' in 属性 else None#答案
        来源列=属性['sources'] if 'sources' in 属性 else None#来源
        来源列表=来源列 if 来源列 is not None else []#空则空表
        if isinstance(答案,str) and 答案!='':#答案
            根.appendChild(处理Markdown文本(window,{'text':答案,'window':window}))
        for 序,源 in enumerate(来源列表):#逐条
            网址=源['url'] if 'url' in 源 and 源['url'] is not None else ''#url
            文=链接标签(网址,源['title'] if 'title' in 源 else None)#标签
            条=文档.createElement('div')
            号=文档.createElement('div')
            号.textContent=str(序+1)
            条.appendChild(号)
            挂链(条,文,安全链接(网址))
            摘=源['snippet'] if 'snippet' in 源 else None#摘录
            if isinstance(摘,str) and 摘!='':
                摘标=文档.createElement('div')
                摘标.textContent=摘
                条.appendChild(摘标)
            日期=源['publishedAt'] if 'publishedAt' in 源 else None#日期
            if isinstance(日期,str) and 日期!='':
                日标=文档.createElement('div')
                日标.textContent=日期
                条.appendChild(日标)
            elif 日期 is not None and isinstance(日期,str) is False:#非串日期
                日标=文档.createElement('div')
                日标.textContent=str(日期)
                条.appendChild(日标)
            根.appendChild(条)
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class 网页块:#web 卡
    'kind=search|fetch'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.根=None

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '拆掉旧卡，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        自身.根=处理网页块(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
