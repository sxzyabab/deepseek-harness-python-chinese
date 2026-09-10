"""自适应目录选择解析：从采样的宿主事实到具体后端 kind 的一次纯决策。

对齐上游 `directory-picker-auto/src/resolve.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '目录选择后端种类','目录选择环境','目录选择宿主事实',
    '解析目录选择后端','环境有值',
]#公开面结束

目录选择后端种类=str#native | browse

def 环境有值(值):#present
    """环境值仅在已设置且非空白时算存在。"""
    return 值 is not None and 值!=''#非空

def 解析目录选择后端(事实):#resolveDirectoryPickerBackend
    """按宿主事实解析应挂的后端 kind。

    native 要求仅环回绑定、非 SSH 拉起、以及可服务的显示会话。
    """
    if 事实.get('bindHost')!='127.0.0.1':#非仅环回
        return 'browse'#远程浏览器可能进来
    if 事实.get('ssh'):#SSH 拉起
        return 'browse'#选择器会开在服务器上
    平台=事实.get('platform')#当前平台
    if 平台=='darwin' or 平台=='win32':#桌面 OS
        return 'native'#默认可服务
    if 平台!='linux' or not 事实.get('linuxChooser'):#非 Linux 或无选择器
        return 'browse'#无法驱动 native
    环境=事实.get('env') or {}#环境子集
    if 环境有值(环境.get('DISPLAY')) or 环境有值(环境.get('WAYLAND_DISPLAY')):#有显示
        return 'native'#Linux native
    return 'browse'#无显示会话

#名义类型别名，便于文档与类型注释
目录选择环境=dict#DISPLAY / WAYLAND_DISPLAY 子集
目录选择宿主事实=dict#bindHost/platform/ssh/env/linuxChooser
