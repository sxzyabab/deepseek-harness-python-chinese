from urllib.parse import quote as 百分编码#地址编码
import re as 正则#地址识别

__all__=['审阅预览地址','是否审阅预览地址']#仅中文公开名

审阅地址模式=正则.compile(r'^dsh-resource://plan-review/[^/?#]+/[^/?#]+$')#审阅预览

def 审阅预览地址(会话标识,请求键):
    """浏览器寿命内命名一次临时审阅。"""
    return 'dsh-resource://plan-review/'+百分编码(会话标识,safe='')+'/'+百分编码(请求键,safe='')#地址

def 是否审阅预览地址(地址):
    """是否临时审阅预览。"""
    return 审阅地址模式.match(地址) is not None#匹配
