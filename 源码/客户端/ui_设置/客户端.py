import threading
from .模式 import 设置模式服务
from .设置镜像 import 设置描述镜像
from .配置表单 import 配置表单集
from .配置表单类型 import 空表单快照
from .开发者工具 import 开发者工具偏好
from .开发者工具设置 import 开发者工具命名空间,开发者工具设置字段,开发者工具设置模式

__all__=['依赖','应用','设置模式服务','设置描述镜像','配置表单集','空表单快照','开发者工具偏好','开发者工具命名空间','开发者工具设置字段','开发者工具设置模式']

依赖=['remote','remote.settings']#远程与远程设置

def 应用(上下文):
    """在一份共享 describe 镜像上提供配置表单服务。"""
    模式=设置模式服务(上下文)#构造模式服务
    持久化='host' if 上下文.remote.$host.isLoopback is True else 'memory'#回环走宿主，否则内存
    镜像=设置描述镜像(上下文,持久化)#构造共享镜像
    def 挂失效():
        """订两路失效并确保首读。"""
        def 重载():
            """文档更新或重连时后台重读。"""
            threading.Thread(target=镜像.加载,daemon=True).start()
        拆表=[
            上下文.remote.$on('settings/document-updated',重载),
            上下文.监听('connection/reset',重载),
        ]
        threading.Thread(target=镜像.确保,daemon=True).start()
        def 拆除():
            """取消订阅。"""
            for 拆 in 拆表:
                拆()
        return 拆除
    上下文.副作用(挂失效,'ui-settings: describe mirror invalidations')
    配置表单集(上下文,{'镜像':镜像,'模式':模式,'持久化':持久化})

inject=依赖
apply=应用
