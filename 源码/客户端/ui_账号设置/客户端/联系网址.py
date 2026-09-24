from urllib.parse import parse_qsl,urlencode,urlparse,urlunparse

__all__=['联系网址']

def 联系网址(配置,上下文):
    """拼出不含认证凭据的问卷地址，并按 Platform Web 票字段预填环境。"""
    解析=urlparse(配置['contactFormUrl'])
    查询=list(parse_qsl(解析.query,keep_blank_values=True))
    比例=上下文['pixelRatio']
    if 比例!=比例 or 比例 is None:
        比例=1
    宽=round(上下文['width']*比例)
    高=round(上下文['height']*比例)
    分辨率=f'{宽}x{高}' if 宽>0 and 高>0 else None
    字段={
        'source':配置['contactSource'],
        'app_version':上下文['version'],
        'os_version':None,
        'device_brand':None,
        'device_model':None,
        'app_locale':上下文['locale'],
        'screen_resolution':分辨率,
    }
    def 删(名):
        """去掉已有同名查询项。"""
        余=[]
        for 键,值 in 查询:
            if 键!=名:
                余.append((键,值))
        查询.clear()
        查询.extend(余)
    def 设(名,值):
        """覆盖或追加一条查询。"""
        删(名)
        查询.append((名,值))
    for 名,值 in 字段.items():
        设('hide_'+名,'1')
        删('prefill_'+名)
        if 值:
            设('prefill_'+名,值)
    删('prefill_uid')
    删('hide_uid')
    return urlunparse((解析.scheme,解析.netloc,解析.path,解析.params,urlencode(查询),解析.fragment))
