__all__=[
    'shell状态字段','shell字节面字段','shell目录项字段','shell统计字段',
    'shell文件系统字段','shell运行结果字段',
]

shell状态字段=('cwd','environment','variables','lastStatus','exitRequested','signal')
shell字节面字段=('stdin','out','err')
shell目录项字段=('name','directory')
shell统计字段=('directory','size','mtimeMs')
shell文件系统字段=('stat','list','readText','writeText','mkdir','remove','rename')
shell运行结果字段=('exitCode','stdout','stderr')
