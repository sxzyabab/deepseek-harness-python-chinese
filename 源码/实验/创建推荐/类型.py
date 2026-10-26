'create_personalized_page 卡片的字段、已记录数据和用户操作'
from typing import Literal,NotRequired,TypedDict

__all__=['创建槽位','页面细节','页面阶段','页面数据','页面动词','页面位置']

创建槽位=Literal['sidebar-right','page','sidebar-left']
页面阶段=Literal['creating','installing','cancelled','installed','kept','removed','failed','interrupted','unconfirmed']
页面动词=Literal['create','keep','undo','cancel','restore']

class 页面细节(TypedDict):
    '技能要求模型写进 details 的字段'
    slot:创建槽位
    initialContent:NotRequired[str]

class 页面数据(TypedDict):
    '每条页面决定记下的数据。已安装的组合包在配置档文件里'
    slot:创建槽位
    customLocation:NotRequired[str]
    bundleName:NotRequired[str]
    application:NotRequired[str]

class 页面位置(TypedDict):
    '卡片随创建和暂不需要送来的字段'
    slot:创建槽位
    customLocation:NotRequired[str]
