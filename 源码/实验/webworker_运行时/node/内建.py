"""Node 兼容性表，集中一处。两个消费者共用，且必须解析到同一模块实例：
  - Worker 的 vite 构建为静态打进 Worker 的代码（自带 loader、Connection 等）
    对这些说明符做别名；
  - Worker 模块加载器在裸名解析之前，从本表应答来自 VFS 加载模块的
    `require('node:fs')`。
此处缺席的项在解析时大声失败，而不是解析成空模块。`process` 故意缺席：
Worker 宿主自行安装该全局，并在装配时填入本表。

导入路径携带分类：`./implemented/<module>` 在 Worker 数据源之上承载
模块的真实语义，而 `./mock/<module>` 是结构性占位，调用时报告缺失能力。
文件名与其 Node 模块说明符完全一致，含嵌套。

每个值都是静态模块工厂，因此加载器仅在 `require` 点名该说明符时
才读表项。工厂推迟的是读表，不是模块求值。

对齐上游 `webworker-runtime/src/node/builtins.ts`。公开面仅中文名。
"""
from .builtin_modules.implemented import async_hooks as 节点异步钩子#async_hooks实现
from .builtin_modules.implemented import buffer as 节点缓冲#buffer实现
from .builtin_modules.implemented import crypto as 节点密码学#crypto实现
from .builtin_modules.mock.dns import promises as 节点dns承诺#dns/promises桩
from .builtin_modules.implemented import events as 节点事件#events实现
from .builtin_modules.implemented import fs as 节点fs#fs实现
from .builtin_modules.implemented.fs import promises as 节点fs承诺#fs/promises实现
from .builtin_modules.implemented import http as 节点http#http实现
from .builtin_modules.implemented import module as 节点模块#module实现
from .builtin_modules.implemented import os as 节点os#os实现
from .builtin_modules.implemented import path as 节点路径#path实现
from .builtin_modules.implemented import perf_hooks as 节点性能钩子#perf_hooks实现
from .builtin_modules.implemented import stream as 节点流#stream实现
from .builtin_modules.implemented.timers import promises as 节点定时器承诺#timers/promises实现
from .builtin_modules.implemented import tty as 节点tty#tty实现
from .builtin_modules.implemented import url as 节点url#url实现
from .builtin_modules.implemented import util as 节点工具#util实现
from .builtin_modules.implemented.util import types as 节点工具类型#util/types实现
from .builtin_modules.implemented import zlib as 节点zlib#zlib实现
from .builtin_modules.implemented import child_process as 节点子进程#child_process实现
from .builtin_modules.mock import net as 节点net#net桩
from .builtin_modules.mock import sqlite as 节点sqlite#sqlite桩
from .builtin_modules.mock import vm as 节点vm#vm桩
from .builtin_modules.mock import worker_threads as 节点工作线程#worker_threads桩
from .external_packages import koffi as koffi包#koffi桩
from .external_packages import node_pty as node_pty包#node-pty桩
from .external_packages import pi_ai as pi_ai包#pi-ai桩
from .external_packages import ripgrep as ripgrep包#ripgrep桩
from .external_packages import sharp as sharp包#sharp桩
from .external_packages import ws as ws包#ws桩
from .external_packages.已替换外部 import 替换外部包清单#替换包清单

__all__=['替换前缀们','创建节点内建']#仅中文公开名

def _工厂(模块):#静态模块工厂
    """返回命名空间对象的工厂。"""
    def 取模块():#推迟读表
        """交回模块。"""
        return 模块#命名空间
    return 取模块#工厂

内建们={#内置说明符表
    'async_hooks':_工厂(节点异步钩子),#异步钩子
    'buffer':_工厂(节点缓冲),#缓冲区
    'child_process':_工厂(节点子进程),#子进程
    'crypto':_工厂(节点密码学),#密码学
    'dns/promises':_工厂(节点dns承诺),#DNS promise面
    'events':_工厂(节点事件),#事件
    'fs':_工厂(节点fs),#文件系统
    'fs/promises':_工厂(节点fs承诺),#fs promise面
    'http':_工厂(节点http),#HTTP
    'module':_工厂(节点模块),#模块辅助
    'net':_工厂(节点net),#网络
    'os':_工厂(节点os),#操作系统
    'path':_工厂(节点路径),#路径
    'path/posix':_工厂(节点路径),#posix路径别名
    'perf_hooks':_工厂(节点性能钩子),#性能钩子
    'sqlite':_工厂(节点sqlite),#sqlite
    'stream':_工厂(节点流),#流
    'timers/promises':_工厂(节点定时器承诺),#定时器promise
    'tty':_工厂(节点tty),#终端
    'url':_工厂(节点url),#URL
    'util':_工厂(节点工具),#工具
    'util/types':_工厂(节点工具类型),#类型谓词
    'vm':_工厂(节点vm),#vm
    'worker_threads':_工厂(节点工作线程),#工作线程
    'zlib':_工厂(节点zlib),#压缩
}#内建们结束

外部们={#外部替换表
    'koffi':_工厂(koffi包),#FFI桥
    'sharp':_工厂(sharp包),#图像
    'node-pty':_工厂(node_pty包),#伪终端
    'ws':_工厂(ws包),#WebSocket
    '@vscode/ripgrep':_工厂(ripgrep包),#ripgrep路径
    '@earendil-works/pi-ai':_工厂(pi_ai包),#pi-ai
}#外部们结束

替换前缀们={#前缀替换表
    '@earendil-works/pi-ai/':_工厂(pi_ai包),#pi-ai子路径
}#替换前缀们结束

#一份清单，两个消费者：此处替换的包也必须排除在 VFS 镜像之外，
#任何分歧在 Worker 启动时失败，而不是在首次 require 时。
_已声明=','.join(sorted(替换外部包清单))#清单排序串
_已接线=','.join(sorted(外部们.keys()))#接线键排序串
if _已声明!=_已接线:#清单与接线不一致
    raise Exception(f'web-preview: replaced-external lists diverge — declared [{_已声明}] vs wired [{_已接线}]')#启动即失败

def 创建节点内建():#构建内置表
    """构建 Worker 模块加载器优先查阅的说明符 → 工厂表。

    返回:
        每个被替换说明符，含其 `node:` 前缀别名。
    """
    表=dict(外部们)#从外部表起步
    for 名,工厂 in 内建们.items():#遍历内置
        表[名]=工厂#裸名
        表[f'node:{名}']=工厂#node:前缀别名
    return 表#返回完整表
