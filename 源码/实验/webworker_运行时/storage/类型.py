"""每个 VFS 后端共享的文件系统接口。已交付实现驻于内存；
浏览器持久化为其注水并消费其已提交的变更流。错误携带 Node 的
`code` 值，因为名册插件按它们分支（可选文件看 `ENOENT`，只读树看 `EACCES`）。

对齐上游 `webworker-runtime/src/storage/types.ts`。公开面仅中文名。
类型面以字段元组与文档描述；实现见 `内存.py`。
"""
__all__=[#仅中文公开名
    'vfs编码','vfs读选项字段','vfs错误字段','vfs统计字段','vfs大整数统计字段',
    'vfs统计选项字段','vfs写选项字段','vfs注水选项字段','vfs目录项字段',
    'vfs目录字段','vfs文件句柄字段','vfs打开文件字段','vfs变更种类','vfs变更汇字段',
]#公开面结束

vfs编码=('utf8','utf-8')#VFS在Node接受任意BufferEncoding处接受的编码
vfs读选项字段=('encoding',)#同步与promise面都接受的读选项字段
vfs错误字段=('code','path','syscall')#带code的Node兼容错误字段
vfs统计字段=(#名册读取的fs.Stats子集字段
    'size','ino','mtimeMs','ctimeMs','atimeMs','birthtimeMs','mtime','mode',#数值与时间
)#统计字段结束
vfs大整数统计字段=(#bigint:true下返回的Stats字段
    'size','mode','dev','ino','nlink',#身份与链接
    'mtimeMs','mtimeNs','ctimeMs','ctimeNs','atimeMs','atimeNs','birthtimeMs','birthtimeNs',#时间
    'mtime','ctime','atime','birthtime',#Date形态
)#大整数统计结束
vfs统计选项字段=('bigint',)#Stat选项；bigint选择大整数形态
vfs写选项字段=('encoding','mode','flag')#名册传入的写选项
vfs注水选项字段=('mode','mtimeMs')#镜像或持久存储注水时的显式元数据
vfs目录项字段=('name','parentPath')#readdir带withFileTypes时报告的目录项
vfs目录字段=('path',)#opendir返回的目录句柄字段
vfs文件句柄字段=()#open返回的文件句柄；方法由实现提供
vfs打开文件字段=('readable','writable','append')#同步Node风格描述符所用的打开文件身份
vfs变更种类=('write','mkdir','remove','chmod')#权威内存文件系统上一次已完成的变更种类
vfs变更汇字段=()#挂到同步VFS上的持久观察者；record/flush由实现提供
