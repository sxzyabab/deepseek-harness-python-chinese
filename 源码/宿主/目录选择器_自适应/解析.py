'按一次启动采样的宿主事实决定挂 native 还是 browse'
from ..web服务器 import 是回环主机#绑定地址是否回环

__all__=[#公开类型与决议
    '目录选择后端种类','目录选择环境','目录选择宿主事实','解析目录选择后端',
]

目录选择后端种类=str#取值 native 或 browse
目录选择环境=dict#DISPLAY 与 WAYLAND_DISPLAY，键可以缺席
目录选择宿主事实=dict#bindHost、allowsRemoteAuthorities、platform、ssh、env、linuxChooser


def 环境有值(环境值):
    '已设置且不是空字符串才算有显示环境。空字符串按未设置'
    if 环境值 is None:#缺席
        return False#没有
    if 环境值=='':#空导出
        return False#没有
    return True#有值


def 解析目录选择后端(事实):
    '没有远程权威、回环绑定、非 SSH，且本机有可服务的显示时为 native，否则为 browse'
    if 事实['allowsRemoteAuthorities'] or not 是回环主机(事实['bindHost']):#远程浏览器进得来
        return 'browse'#应用内浏览
    if 事实['ssh']:#转发的连接开不了服务器上的选择器
        return 'browse'#应用内浏览
    平台=事实['platform']#宿主平台
    if 平台=='darwin' or 平台=='win32':#这两种系统视为有显示
        return 'native'#系统选择器
    if 平台!='linux' or not 事实['linuxChooser']:#不是 linux，或没有选择器二进制
        return 'browse'#应用内浏览
    环境=事实['env']#显示环境。DISPLAY 与 WAYLAND_DISPLAY 可以缺席
    if 环境有值(环境.get('DISPLAY')) or 环境有值(环境.get('WAYLAND_DISPLAY')):#任一非空即有显示
        return 'native'#系统选择器
    return 'browse'#没有显示
