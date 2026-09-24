from .文案 import 命名空间,中文,英文
from .智能体循环卡片 import 智能体循环卡片
from .智能体循环卡片控制器 import 智能体循环命名空间,智能体循环卡片控制器

__all__=['依赖','应用','命名空间','中文','英文','智能体循环命名空间','智能体循环卡片控制器']

依赖=['slots','locale','configForms']

def 应用(上下文):
    """Host 服务 agent-loop 命名空间期间，把本页登记进 plugins.item。"""
    翻译=上下文.locale.bind(命名空间)
    def 登记词典():
        """登记本页词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-settings-agent-loop: dictionaries')
    卡片=智能体循环卡片控制器(上下文.configForms.get(智能体循环命名空间))
    def 拆表单():
        """拆除表单订阅。"""
        def 拆():
            """dispose。"""
            卡片.拆除()
        return 拆
    上下文.副作用(拆表单,'ui-settings-agent-loop: form subscription')
    def 挂页():
        """命名空间被服务时注入插件页。"""
        def 登记():
            """登记 plugins.item。"""
            def 标签():
                """页标题。"""
                return 翻译('title')
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'agent-loop',
                'order':20,
                'label':标签,
                'locale':命名空间,
                'inject':卡片.注入,
            },智能体循环卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        """whileServed。"""
        return 上下文.configForms.whileServed([智能体循环命名空间],挂页)
    上下文.副作用(监视,'ui-settings-agent-loop: page')

inject=依赖
apply=应用
