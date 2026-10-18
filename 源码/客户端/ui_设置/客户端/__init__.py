from . import 开发者工具
from . import 模式
from . import 设置镜像
from . import 配置表单
from . import 配置表单类型
from . import 约定

__all__=['开发者工具','模式','设置镜像','配置表单','配置表单类型','约定','依赖','应用']

依赖=['remote','remote.settings']

def 应用(上下文,配置=None):
    '提供共享表单，并在文档变更和重连时刷新描述镜像'
    模式服务=模式.设置模式服务(上下文)
    镜像=设置镜像.设置描述镜像(上下文)

    def 挂失效():
        '订上文档更新和重连，并做第一次读取'
        def 重载():
            '文档更新或重连时重读'
            镜像.加载()
        拆表=[
            getattr(上下文.remote,'$on')('settings/document-updated',重载),
            上下文.监听('connection/reset',重载),
        ]
        镜像.确保()

        def 拆除():
            '取消这两路订阅'
            for 拆 in 拆表:
                拆()

        return 拆除

    上下文.副作用(挂失效,'ui-settings: describe mirror invalidations')
    配置表单.配置表单集(上下文,{'镜像':镜像,'模式':模式服务})

inject=依赖
apply=应用
