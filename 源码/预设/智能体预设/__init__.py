from ...依赖.schemastery import 字符串字段,数字字段,列表字段,任意字段
from ...依赖.loader.插件组 import 标记为组插件

配置={
    'id':字符串字段(可空=False),
    'name':字符串字段(),
    'description':字符串字段(),
    'order':数字字段(),
    'plugins':列表字段(任意字段(),可空=False),
}

class 智能体预设:
    """向预设注册表提交子插件配置，不接管使用旧修订的智能体。"""
    inject=['agentPresets']
    Config=配置

    def __init__(自身,ctx,配置值):
        """记下上下文与配置。"""
        自身.ctx=ctx
        自身.配置=配置值

    def 初始化(自身):
        """向注册表登记本行，产出拆除器。"""
        yield 自身.ctx.agentPresets.注册(自身.配置)

标记为组插件(智能体预设)
__all__=['智能体预设','配置']
inject=['agentPresets']
Config=配置
default=智能体预设
