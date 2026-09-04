"""packer 与 worker 宿主共享的镜像布局契约：虚拟根、组合配置与 manifest
在镜像内的位置，以及每个镜像都携带的空工作目录。一份定义，两个
消费者——packer 写出此布局，worker 宿主挂载它。

对齐上游 `webworker-runtime/src/image-layout.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '默认根','镜像文件名','镜像配置路径','镜像清单路径','镜像主目录',
    '镜像空目录们','镜像覆盖目录们','降低版本','包装参数们',
]#公开面结束

默认根='/dsh'#默认虚拟根；运行时除非另有说明否则在此挂载镜像
镜像文件名='vfs-image.tar.gz'#打包基础镜像的叶名：持有ustar归档的gzip成员
镜像配置路径='config/cordis.yml'#组合profile写入的镜像路径；Loader读取
镜像清单路径='config/vfs-manifest.json'#运行时在包装单个模块前读取的manifest镜像路径
镜像主目录='home'#根下的home目录；process shim的DSH_HOME/HOME默认
镜像空目录们=['home/','workspace/','tmp/']#宿主树期望存在且为空的工作目录
镜像覆盖目录们=['home','workspace']#overlay归档可填充的顶层目录
降低版本='dsh-worker-transform/1'#降低后代码形状身份；变更WRAPPER_PARAMS须递增
包装参数们=(#降低后的体从其包装器按序期望的自由变量
    'exports','require','module','__filename','__dirname','__dsh$meta','__als',#按序形参名
)#包装参数结束
