'enable_official_plugin 卡片的字段、已记录数据和目录文本'
from typing import Literal,NotRequired,TypedDict

__all__=['插件细节','插件阶段','插件数据']

class 插件细节(TypedDict):
    '技能要求模型写进 details 的字段'
    name:str

插件阶段=Literal['enabled','already-enabled','failed','unconfirmed']

class 插件数据(TypedDict):
    '每条插件决定记下的数据。真正的配置在配置档文件里'
    application:NotRequired[Literal['restart-required']]
    errorCode:NotRequired[str]
