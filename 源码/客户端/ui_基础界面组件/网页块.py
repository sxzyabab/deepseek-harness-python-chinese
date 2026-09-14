
__all__=['网页块','安全链接','链接标签']#仅中文公开名

def 安全链接(网址):
    """仅 http(s)；否则 None 走纯文本。"""
    if isinstance(网址,str) is False or 网址=='':#空
        return None#无
    低=网址.lower()#小写
    if 低.startswith('http://') or 低.startswith('https://'):#协议
        if '://' not in 网址:#畸形
            return None#无
        return 网址#可用
    return None#非 http

def 链接标签(网址,标题):
    """有标题用标题；否则主机名；再否则原文。"""
    if isinstance(标题,str) and 标题!='':#有标题
        return 标题#标题
    余=网址.split('://',1)[-1]#去协议
    主机=余.split('/',1)[0].split('?',1)[0].split('#',1)[0]#主机
    return 主机 if 主机!='' else 网址#主机或原文

class 网页块:#web 卡
    """kind=search|fetch。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """按 kind 产出。"""
        属性=自身.属性#props
        种=属性['kind'] if 'kind' in 属性 else None#种
        截断=属性['truncated'] is True if 'truncated' in 属性 else False#截断
        类名=属性['className'] if 'className' in 属性 else None#类
        if 种=='fetch':#抓取
            网址=属性['url'] if 'url' in 属性 and 属性['url'] is not None else ''#url
            return {#抓取卡
                'type':'web-block','kind':'fetch',#类型
                'url':网址,#url
                'href':安全链接(网址),#安全 href
                'label':网址,#标签
                'statusCode':属性['statusCode'] if 'statusCode' in 属性 else None,#状态码
                'truncated':截断,#截断
                'className':类名,#类
                'cssModule':'网页块.module.css',#样式
            }#结束
        答案=属性['answer'] if 'answer' in 属性 else None#答案
        来源列=属性['sources'] if 'sources' in 属性 else None#来源
        来源列表=来源列 if 来源列 is not None else []#空则空表
        空=(答案 is None or 答案=='') and len(来源列表)==0#空卡；判 length
        项列表=[]#来源项
        for 序,源 in enumerate(来源列表):#逐条
            网址=源['url'] if 'url' in 源 and 源['url'] is not None else ''#url
            项列表.append({#项
                'ordinal':序+1,#1 基序号
                'url':网址,#url
                'href':安全链接(网址),#href
                'label':链接标签(网址,源['title'] if 'title' in 源 else None),#标签
                'snippet':源['snippet'] if 'snippet' in 源 else None,#摘录
                'publishedAt':源['publishedAt'] if 'publishedAt' in 源 else None,#日期
            })#项结束
        return {#检索卡
            'type':'web-block','kind':'search',#类型
            'answer':答案,#答案 md
            'sources':项列表,#来源
            'empty':空,#空
            'truncated':截断,#截断
            'className':类名,#类
            'cssModule':'网页块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
