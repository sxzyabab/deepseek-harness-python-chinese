"""按宿主采样事实决定挂 native 还是 browse 后端。"""
__all__=[
    '目录选择后端种类','目录选择环境','目录选择宿主事实',
    '解析目录选择后端','环境有值',
]

目录选择后端种类=str#取值 native 或 browse

def 环境有值(值):
    """环境值仅在已设置且非空白时算存在。"""
    return 值 is not None and 值!=''

def 解析目录选择后端(事实):
    """按宿主事实解析应挂的后端种类。

    native 要求仅环回绑定、非 SSH 拉起、以及可服务的显示会话。
    """
    if 事实.get('bindHost')!='127.0.0.1':#非仅环回则远程浏览器可能进来
        return 'browse'
    if 事实.get('ssh'):#SSH 拉起时选择器会开在服务器上
        return 'browse'
    平台=事实.get('platform')
    if 平台=='darwin' or 平台=='win32':
        return 'native'
    if 平台!='linux' or not 事实.get('linuxChooser'):
        return 'browse'
    环境=事实.get('env') or {}
    if 环境有值(环境.get('DISPLAY')) or 环境有值(环境.get('WAYLAND_DISPLAY')):
        return 'native'
    return 'browse'

目录选择环境=dict#DISPLAY / WAYLAND_DISPLAY 子集
目录选择宿主事实=dict#bindHost/platform/ssh/env/linuxChooser
