'把当前应用色板写进平台授权链接'

__all__=['授权网址带主题']

def 授权网址带主题(授权网址,色板):
    '在宿主已经放上的参数之外，加上 theme=light 或 theme=dark'
    from urllib.parse import parse_qsl,urlencode,urlsplit,urlunsplit
    拆开=urlsplit(授权网址)
    查询=parse_qsl(拆开.query,keep_blank_values=True)
    留下=[]
    for 键,值 in 查询:
        if 键!='theme':
            留下.append((键,值))
    留下.append(('theme',色板))
    return urlunsplit((拆开.scheme,拆开.netloc,拆开.path,urlencode(留下),拆开.fragment))
