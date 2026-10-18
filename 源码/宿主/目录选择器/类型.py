'目录选择缝的浏览一层长什么样。只有结构，没有运行时'
from typing import TypedDict as 类型字典#结构类型

__all__=['目录项','目录列表']#仅中文公开名


class 目录项(类型字典):#一行目录或面包屑
    '浏览器一行。根屑的 name 用完整路径，path 一律是宿主绝对路径'
    name:str#显示名。根面包屑携带完整路径
    path:str#宿主绝对路径。客户端不自己拼接路径段
    hidden:bool#按宿主平台惯例隐藏。点开头在 POSIX 上为真。客户端决定是否显示


class 目录列表(类型字典):#一层加祖先
    '一层目录，加上从文件系统根到该目录的祖先'
    path:str#被列目录的绝对路径
    home:str#宿主账户家目录，供面包屑 Home 落根
    crumbs:list#从文件系统根到被列目录，含自身。每一屑都可跳转，hidden 恒为假
    entries:list#直属子目录，按名排序，含指向目录的符号链接
    truncated:bool#entries 被完整结果上限截断时为真。缺的是按名排序的尾部，隐藏行也计入上限
