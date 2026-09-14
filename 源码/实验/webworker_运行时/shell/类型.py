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
