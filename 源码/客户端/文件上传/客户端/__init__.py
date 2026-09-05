"""浏览器后台上传 Cordis 服务。

对齐上游 `file-upload/src/client/index.ts`。公开面仅中文名。
"""
from .运行时 import 文件上传运行时#上传运行时服务
from .约定 import 文件上传服务协议#服务契约
from ..类型 import 文件上传凭证标识#凭证品牌

__all__=[#仅中文公开名
    '注入',
    '应用',
    'apply',
    '文件上传运行时',
    '文件上传服务协议',
    '文件上传凭证标识',
]#公开面结束

注入=['remote']#硬依赖 remote
inject=注入#上游名

def 应用(上下文):#客户端插件体
    """提供浏览器后台上传服务。"""
    上下文.plugin(文件上传运行时)#挂上运行时服务

apply=应用#上游名
