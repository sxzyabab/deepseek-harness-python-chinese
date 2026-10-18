from . import 文案
from . import 应用
from . import 服务
from . import 存储
from . import 草稿
from . import 视图选中项
from . import 上下文占用
from . import 图像标签
from . import 停止序列
from . import 停止快捷键
from . import 骨架
from . import 输入
from . import 用户文本
from . import 会话
from . import 队列
from . import 设置
from . import 约定
from .应用 import 应用 as 登记应用
from .应用 import 依赖
from .应用 import 配置
from .服务 import 会话控制器
from .会话.装配 import 界面会话

__all__=[
    '文案','应用','服务','存储','草稿','视图选中项','上下文占用','图像标签',
    '停止序列','停止快捷键','骨架','输入','用户文本','会话','队列','设置','约定',
    '依赖','配置','登记应用','会话控制器','界面会话',
]

命名空间=文案.命名空间
inject=依赖
apply=登记应用
