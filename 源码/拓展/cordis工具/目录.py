"""再导出：目录查询面对齐 `接口目录.py`，数据体来自 `目录数据`。"""
from .接口目录 import (#查询面
    服务目录,事件目录,类型目录,继承上下文目录,
    查询服务目录,查询事件目录,
)#公开面
from .目录数据 import 上游目录路径#数据源路径

SERVICE_API=服务目录#上游名
EVENT_API=事件目录#上游名
TYPE_API=类型目录#上游名
INHERITED_CTX_API=继承上下文目录#上游名
queryServiceApi=查询服务目录#上游名
queryEventApi=查询事件目录#上游名

__all__=[#公开面
    '服务目录','事件目录','类型目录','继承上下文目录',
    '查询服务目录','查询事件目录','上游目录路径',
    'SERVICE_API','EVENT_API','TYPE_API','INHERITED_CTX_API',
    'queryServiceApi','queryEventApi',
]#结束
