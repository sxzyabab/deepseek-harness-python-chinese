"""网页检索/抓取完成面。

对齐上游 `ui-primitives/src/WebBlock.tsx`。公开面仅中文名。
仅 http(s) 成外链；search/fetch 两种 kind。
"""

__all__=['网页块','安全链接','链接标签']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 安全链接(网址):#可导航 href
    """仅 http(s)；否则 None 走纯文本。"""
    if not isinstance(网址,str) or 网址=='':#空
        return None#无
    低=网址.lower()#小写
    if 低.startswith('http://') or 低.startswith('https://'):#协议
        try:#粗校验
            if '://' not in 网址:#畸形
                return None#无
            return 网址#可用
        except Exception:#解析失败
            return None#无
    return None#非 http

def 链接标签(网址,标题):#可见标签
    """有标题用标题；否则主机名；再否则原文。"""
    if isinstance(标题,str) and 标题!='':#有标题
        return 标题#标题
    try:#拆主机
        余=网址.split('://',1)[-1]#去协议
        主机=余.split('/',1)[0].split('?',1)[0].split('#',1)[0]#主机
        return 主机 if 主机!='' else 网址#主机或原文
    except Exception:#失败
        return 网址#原文

class 网页块:#web 卡
    """kind=search|fetch。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """按 kind 产出。"""
        属性=自身.属性#props
        种=取字段(属性,'kind')#种
        截断=bool(取字段(属性,'truncated'))#截断
        if 种=='fetch':#抓取
            网址=取字段(属性,'url') or ''#url
            return {#抓取卡
                'type':'web-block','kind':'fetch',#类型
                'url':网址,#url
                'href':安全链接(网址),#安全 href
                'label':网址,#标签
                'statusCode':取字段(属性,'statusCode'),#状态码
                'truncated':截断,#截断
                'className':取字段(属性,'className'),#类
                'cssModule':'网页块.module.css',#样式
            }#结束
        答案=取字段(属性,'answer')#答案
        来源们=取字段(属性,'sources') or []#来源
        空=(答案 is None or 答案=='') and len(来源们)==0#空卡
        项们=[]#来源项
        for 序,源 in enumerate(来源们):#逐条
            网址=取字段(源,'url') or ''#url
            项们.append({#项
                'ordinal':序+1,#1 基序号
                'url':网址,#url
                'href':安全链接(网址),#href
                'label':链接标签(网址,取字段(源,'title')),#标签
                'snippet':取字段(源,'snippet'),#摘录
                'publishedAt':取字段(源,'publishedAt'),#日期
            })#项结束
        return {#检索卡
            'type':'web-block','kind':'search',#类型
            'answer':答案,#答案 md
            'sources':项们,#来源
            'empty':空,#空
            'truncated':截断,#截断
            'className':取字段(属性,'className'),#类
            'cssModule':'网页块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
