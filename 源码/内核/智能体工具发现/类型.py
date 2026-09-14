from typing import Literal,TypedDict#字面量与结构类型

__all__=('工具展示模式','插件配置')#仅中文公开名

工具展示模式=Literal['native','code','both']#模型看到的工具形态：native 全部 schema；code 仅 run_code+SDK；both 两者都发

class 插件配置(TypedDict):#本行插件配置
    """插件配置。`mode` 必填：不带本行的预设本来就会拿到部署默认值，省略它等于这一行白组装了。"""
    mode:工具展示模式#本 Agent 的模型看到的形态
