"""自适应目录选择组合的启动时后端解析与 PATH 探测。

对齐上游 `directory-picker-auto` 的 resolve/probe。公开面仅中文名；后端 kind 字面量保持上游。
"""
import os,sys#环境与平台

__all__=[#仅中文公开名
    '目录选择后端种类',
    '解析目录选择后端',
    '可执行',
    '有Linux选择器二进制',
    'Linux选择器二进制们',
]#公开面结束

目录选择后端种类=('native','browse')#可选后端
Linux选择器二进制们=('zenity','kdialog')#Linux 选择器名表

def 已设置(值):#环境值是否存在
    """环境值仅在已设置且非空白时算存在。"""
    return 值 is not None and 值!=''#非空

def 解析目录选择后端(事实):#按宿主事实解析后端 kind
    """native 要求仅环回、无 SSH、可服务显示会话；否则 browse。"""
    if 取字段(事实,'bindHost')!='127.0.0.1':#非仅环回
        return 'browse'#远程可能进来
    环境=取字段(事实,'env') or {}#环境子集
    if 已设置(取字段(环境,'SSH_CONNECTION')) or 已设置(取字段(环境,'SSH_TTY')):#SSH 拉起
        return 'browse'#选择器会开在服务器上
    平台=取字段(事实,'platform')#进程平台
    if 平台=='darwin' or 平台=='win32':#macOS/Windows
        return 'native'#默认有显示会话
    if 平台!='linux' or not 取字段(事实,'linuxChooser'):#非 Linux 或无选择器
        return 'browse'#无法驱动 native
    if 已设置(取字段(环境,'DISPLAY')) or 已设置(取字段(环境,'WAYLAND_DISPLAY')):#有显示会话
        return 'native'#Linux native
    return 'browse'#无显示则 browse

def 可执行(候选):#路径是否对本进程可执行
    """仅当该路径存在且可执行时为 True。"""
    return os.path.isfile(候选) and os.access(候选,os.X_OK)#存在且可执行

def 有Linux选择器二进制(路径值,是否可执行=None):#PATH 上是否有选择器
    """在一段 PATH 值里扫描 zenity/kdialog。"""
    if 是否可执行 is None:#缺省谓词
        是否可执行=可执行#生产谓词
    分隔=os.pathsep#平台 PATH 分隔符
    for 目录 in (路径值 or '').split(分隔):#拆 PATH
        if 目录=='':#空段
            continue#跳过
        for 名 in Linux选择器二进制们:#逐个试
            if 是否可执行(os.path.join(目录,名)):#命中
                return True#有
    return False#没有

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性
