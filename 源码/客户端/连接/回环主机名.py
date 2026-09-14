import re#段数字校验

__all__=['是否回环主机名']#仅中文公开名

段规则=re.compile(r'^[0-9]{1,3}\Z')#每段 0–255 的十进制

def 是否回环主机名(主机名):#是否回环主机名
    """归一化后的 URL 主机名是否点名本地回环权威。"""
    if 主机名=='localhost' or 主机名=='[::1]':#本机名或 IPv6 回环
        return True#回环
    段列表=主机名.split('.')#按点切开
    if len(段列表)!=4:#必须四段
        return False#非 IPv4
    if 段列表[0]!='127':#127/8
        return False#非回环网段
    for 段 in 段列表:#每段
        if 段规则.fullmatch(段) is None:#非纯数字段
            return False#非法
        if int(段)>255:#超字节
            return False#非法
    return True#127/8 回环
