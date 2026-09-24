from urllib.parse import parse_qsl,urlencode,urlparse,urlunparse

__all__=['带主题的授权网址']

def 带主题的授权网址(授权网址,配色):
    """把 Desktop 已解析配色写进授权链接，不丢掉 Host 已放上的参数。"""
    解析=urlparse(授权网址)
    查询=list(parse_qsl(解析.query,keep_blank_values=True))
    余=[]
    for 键,值 in 查询:
        if 键!='theme':
            余.append((键,值))
    余.append(('theme',配色))
    return urlunparse((解析.scheme,解析.netloc,解析.path,解析.params,urlencode(余),解析.fragment))
