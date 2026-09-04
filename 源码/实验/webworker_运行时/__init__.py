"""仅浏览器宿主运行时：dedicated Web Worker 内的 harness Cordis 树。

对齐上游 `webworker-runtime/src/index.ts`。公开面仅中文名。
"""
from .polyfill.async_context.als运行时 import 创建als运行时#ALS运行时工厂
from .transport.帧 import 解析入站帧#解析入站帧
from .module_system.模块加载器 import (#模块加载器面
    默认条件们,要求活动模块加载器,设活动模块加载器,工作线程模块加载器,
)#模块系统
from .module_system import posix路径#POSIX路径工具
from .transport.合成http import 创建合成交换#合成HTTP交换
from .compile.变换 import 降低模块源#模块降低
from .transport.隧道 import api前缀,合成主机,隧道服务器#隧道服务器面
from .工作线程宿主 import 创建工作线程宿主,默认根 as _宿主默认根#Worker宿主面
from .镜像布局 import (#镜像布局常量
    默认根,镜像配置路径,镜像空目录们,镜像文件名,镜像主目录,
    镜像清单路径,镜像覆盖目录们,降低版本,包装参数们,
)#镜像布局
from .fixture清单 import (#fixture目录面
    解析预览fixture清单,预览fixture清单文件,预览fixture清单版本,
)#fixture manifest
from .storage.内存 import 加载vfs镜像,加载vfs覆盖层,内存vfs#内存VFS
from .storage.镜像gzip import 解压镜像,流式解压镜像#镜像解压
from .storage.活动 import 要求活动vfs,设活动vfs#活动VFS槽
from .storage import 类型 as vfs类型#VFS类型面

__all__=[#仅中文公开名
    '创建als运行时','解析入站帧',
    '默认条件们','要求活动模块加载器','设活动模块加载器','工作线程模块加载器',
    'posix路径','创建合成交换','降低模块源',
    'api前缀','合成主机','隧道服务器',
    '创建工作线程宿主',
    '默认根','镜像配置路径','镜像空目录们','镜像文件名','镜像主目录',
    '镜像清单路径','镜像覆盖目录们','降低版本','包装参数们',
    '解析预览fixture清单','预览fixture清单文件','预览fixture清单版本',
    '加载vfs镜像','加载vfs覆盖层','内存vfs',
    '解压镜像','流式解压镜像',
    '要求活动vfs','设活动vfs',
]#公开面结束
