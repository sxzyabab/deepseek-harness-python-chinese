'按宿主采样事实决定挂 native 还是 browse 后端'
import ipaddress,re#环回地址判定
__all__=[
    '目录选择后端种类','目录选择环境','目录选择宿主事实',
    '解析目录选择后端','环境有值','是环回主机',
]

_四段尾=re.compile(r'^(.*:)(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')#IPv6 点分尾

def _十六进制尾(主机):#把点分尾收成两个十六进制组
    '让 ::0.0.0.1 按套接字绑定的低 32 位来读'
    匹配=_四段尾.match(主机)#尾
    if 匹配 is None:#没有点分尾
        return 主机#原样
    段=[int(匹配.group(下标)) for 下标 in (2,3,4,5)]#四段
    if any(值>255 for 值 in 段):#非法
        return 主机#交给后续解析失败
    高=(段[0]<<8)|段[1]#高组
    低=(段[2]<<8)|段[3]#低组
    return 匹配.group(1)+format(高,'x')+':'+format(低,'x')#拼回

def 是环回主机(主机):#绑定地址是否环回
    '127/8、::1，以及它们的 IPv4 映射；非字面量不是环回'
    if not isinstance(主机,str) or 主机=='':#没有地址
        return False#不是
    区=主机.find('%')#接口区
    裸=主机 if 区<0 else 主机[:区]#去掉区
    try:#解析字面量
        地址=ipaddress.ip_address(_十六进制尾(裸))#地址
    except ValueError:#不是字面量
        return False#不是环回
    if isinstance(地址,ipaddress.IPv6Address) and 地址.ipv4_mapped is not None:#映射
        地址=地址.ipv4_mapped#按 IPv4
    return bool(地址.is_loopback)#环回段

目录选择后端种类=str#取值 native 或 browse

def 环境有值(值):
    '环境值仅在已设置且非空白时算存在'
    return 值 is not None and 值!=''

def 解析目录选择后端(事实):
    """按宿主事实解析应挂的后端种类。

    native 要求没有远程权威、环回绑定、非 SSH 拉起、以及可服务的显示会话
    """
    if 事实.get('allowsRemoteAuthorities') or not 是环回主机(事实.get('bindHost')):#远程浏览器进得来
        return 'browse'
    if 事实.get('ssh'):#SSH 拉起时选择器会开在服务器上
        return 'browse'
    平台=事实.get('platform')
    if 平台=='darwin' or 平台=='win32':
        return 'native'
    if 平台!='linux' or not 事实.get('linuxChooser'):
        return 'browse'
    环境=事实.get('env')
    if not isinstance(环境,dict):#缺席才补空表；空表本身仍要保留
        环境={}
    if 环境有值(环境.get('DISPLAY')) or 环境有值(环境.get('WAYLAND_DISPLAY')):
        return 'native'
    return 'browse'

目录选择环境=dict#DISPLAY / WAYLAND_DISPLAY 子集
目录选择宿主事实=dict#bindHost/allowsRemoteAuthorities/platform/ssh/env/linuxChooser
