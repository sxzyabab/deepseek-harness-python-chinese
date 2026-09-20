from .未实现失败 import 运行时错误
from .builtin_modules.implemented import async_hooks as 节点异步钩子
from .builtin_modules.implemented import buffer as 节点缓冲
from .builtin_modules.implemented import crypto as 节点密码学
from .builtin_modules.mock.dns import promises as 节点域名承诺
from .builtin_modules.implemented import events as 节点事件
from .builtin_modules.implemented import fs as 节点文件
from .builtin_modules.implemented.fs import promises as 节点文件承诺
from .builtin_modules.implemented import http as 节点超文本
from .builtin_modules.implemented import module as 节点模块
from .builtin_modules.implemented import os as 节点系统
from .builtin_modules.implemented import path as 节点路径
from .builtin_modules.implemented import perf_hooks as 节点性能钩子
from .builtin_modules.implemented import stream as 节点流
from .builtin_modules.implemented.timers import promises as 节点定时器承诺
from .builtin_modules.implemented import tty as 节点终端
from .builtin_modules.implemented import url as 节点网址
from .builtin_modules.implemented import util as 节点工具
from .builtin_modules.implemented.util import types as 节点工具类型
from .builtin_modules.implemented import zlib as 节点压缩
from .builtin_modules.implemented import child_process as 节点子进程
from .builtin_modules.mock import net as 节点网络
from .builtin_modules.mock import sqlite as 节点数据库
from .builtin_modules.mock import vm as 节点虚拟机
from .builtin_modules.mock import worker_threads as 节点工作线程
from .external_packages import koffi as 外函数包
from .external_packages import libreoffice_kit as 办公套件包
from .external_packages import node_addon_system_flock as 文件锁包
from .external_packages import node_pty as 伪终端包
from .external_packages import execa as 执行包
from .external_packages import pi_ai as 派智能包
from .external_packages import ripgrep as 正则搜索包
from .external_packages import sharp as 图像包
from .external_packages import ws as 套接字包
from .external_packages.已替换外部 import 替换外部包清单

__all__=['替换前缀表','创建节点内建']

def _工厂(模块):
    """返回命名空间对象的工厂。"""
    def 取模块():
        """交回模块。"""
        return 模块
    return 取模块

内建表={
    'async_hooks':_工厂(节点异步钩子),
    'buffer':_工厂(节点缓冲),
    'child_process':_工厂(节点子进程),
    'crypto':_工厂(节点密码学),
    'dns/promises':_工厂(节点域名承诺),
    'events':_工厂(节点事件),
    'fs':_工厂(节点文件),
    'fs/promises':_工厂(节点文件承诺),
    'http':_工厂(节点超文本),
    'module':_工厂(节点模块),
    'net':_工厂(节点网络),
    'os':_工厂(节点系统),
    'path':_工厂(节点路径),
    'path/posix':_工厂(节点路径),
    'perf_hooks':_工厂(节点性能钩子),
    'sqlite':_工厂(节点数据库),
    'stream':_工厂(节点流),
    'timers/promises':_工厂(节点定时器承诺),
    'tty':_工厂(节点终端),
    'url':_工厂(节点网址),
    'util':_工厂(节点工具),
    'util/types':_工厂(节点工具类型),
    'vm':_工厂(节点虚拟机),
    'worker_threads':_工厂(节点工作线程),
    'zlib':_工厂(节点压缩),
}

外部表={
    '@deepseek-ai/libreoffice-kit':_工厂(办公套件包),
    '@deepseek-ai/node-addon-system/flock':_工厂(文件锁包),
    'koffi':_工厂(外函数包),
    'sharp':_工厂(图像包),
    'node-pty':_工厂(伪终端包),
    'execa':_工厂(执行包),
    'ws':_工厂(套接字包),
    '@vscode/ripgrep':_工厂(正则搜索包),
    '@earendil-works/pi-ai':_工厂(派智能包),
}

替换前缀表={
    '@earendil-works/pi-ai/':_工厂(派智能包),
}

#一份清单，两个消费者：此处替换的包也必须排除在 VFS 镜像之外，
#任何分歧在 Worker 启动时失败，而不是在首次 require 时。
_已声明=','.join(sorted(替换外部包清单))
_已接线=','.join(sorted(外部表.keys()))
if _已声明!=_已接线:
    raise 运行时错误(f'web-preview: 已替换外部包清单不一致 — 声明 [{_已声明}] 对接线 [{_已接线}]')

def 创建节点内建():
    """构建 Worker 模块加载器优先查阅的说明符 → 工厂表。

    返回:
        每个被替换说明符，含其 `node:` 前缀别名。
    """
    表=dict(外部表)
    for 名,工厂 in 内建表.items():
        表[名]=工厂
        表[f'node:{名}']=工厂
    return 表
