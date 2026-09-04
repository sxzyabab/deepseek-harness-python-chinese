"""worker 内 shell 的类型：一行命令会改动的状态、程序读写的字节面，以及命令表
存放的程序签名。浏览器 worker 没有进程，因此「程序」就是作用于 VFS 的
函数，下方状态就是整台机器。

对齐上游 `webworker-runtime/src/shell/types.ts`。公开面仅中文名。
类型面以字段元组与文档描述；实现见解释与 programs。
"""
__all__=[#仅中文公开名
    'shell状态字段','shell字节面字段','shell目录项字段','shell统计字段',
    'shell文件系统字段','shell运行结果字段',
]#公开面结束

shell状态字段=('cwd','environment','variables','lastStatus','exitRequested','signal')#可变状态字段
shell字节面字段=('stdin','out','err')#程序字节面字段
shell目录项字段=('name','directory')#目录项字段
shell统计字段=('directory','size','mtimeMs')#路径统计字段
shell文件系统字段=('stat','list','readText','writeText','mkdir','remove','rename')#文件系统面字段
shell运行结果字段=('exitCode','stdout','stderr')#一行运行结果字段
