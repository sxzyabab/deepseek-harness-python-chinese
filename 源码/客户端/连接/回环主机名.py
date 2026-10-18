'浏览器和宿主共用的回环主机名判断'
import re#四段数字

段规则=re.compile(r'^[0-9]{1,3}\Z')#一段十进制


def 是否回环主机名(主机名):
    '归一化后的 URL 主机名是否点名本地回环。IPv6 回环保留方括号'
    if 主机名=='localhost' or 主机名=='[::1]':#本机名或 IPv6 回环
        return True#是回环
    段=主机名.split('.')#按点拆开
    if len(段)!=4 or 段[0]!='127':#不是四段，或不是 127 开头
        return False#不是 IPv4 回环
    for 片 in 段:#每一段
        if 段规则.fullmatch(片) is None or int(片)>255:#不是 0 到 255
            return False#拒绝
    return True#127/8 整段
