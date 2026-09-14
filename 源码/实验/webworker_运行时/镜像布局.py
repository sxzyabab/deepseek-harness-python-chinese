__all__=[#仅中文公开名
    '默认根','镜像文件名','镜像配置路径','镜像清单路径','镜像主目录',
    '镜像空目录列表','镜像覆盖目录列表','降低版本','包装参数列表',
]#公开面结束

默认根='/dsh'#默认虚拟根；运行时除非另有说明否则在此挂载镜像
镜像文件名='vfs-image.tar.gz'#打包基础镜像的叶名：持有ustar归档的gzip成员
镜像配置路径='config/cordis.yml'#组合profile写入的镜像路径；Loader读取
镜像清单路径='config/vfs-manifest.json'#运行时在包装单个模块前读取的manifest镜像路径
镜像主目录='home'#根下的home目录；process shim的DSH_HOME/HOME默认
镜像空目录列表=['home/','workspace/','tmp/']#宿主树期望存在且为空的工作目录
镜像覆盖目录列表=['home','workspace']#overlay归档可填充的顶层目录
降低版本='dsh-worker-transform/1'#降低后代码形状身份；变更WRAPPER_PARAMS须递增
包装参数列表=(#降低后的体从其包装器按序期望的自由变量
    'exports','require','module','__filename','__dirname','__dsh$meta','__als',#按序形参名
)#包装参数结束
