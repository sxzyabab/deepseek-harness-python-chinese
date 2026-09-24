from .文案 import 命名空间,中文,英文
from .子智能体卡片 import 子智能体卡片
from .子智能体卡片控制器 import 子智能体卡片面
from .子智能体限额卡片控制器 import 子智能体限额卡片控制器
from .子智能体模型选择卡片控制器 import 子智能体模型选择命名空间,子智能体模型选择卡片控制器

__all__=[
    '依赖','应用','命名空间','中文','英文',
    '子智能体命名空间','子智能体模型选择命名空间',
    '子智能体限额卡片控制器','子智能体模型选择卡片控制器',
]

子智能体命名空间='subagent'
依赖=['slots','locale','remote','remote.session','configForms']

def 应用(上下文):
    """Host 服务限额或模型选择命名空间期间，把本页登记进 plugins.item。"""
    翻译=上下文.locale.bind(命名空间)
    def 登记词典():
        """登记本页词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-settings-subagent: dictionaries')
    限额=子智能体限额卡片控制器(上下文.configForms.get(子智能体命名空间))
    def 拆限额():
        """拆除限额订阅。"""
        def 拆():
            """dispose。"""
            限额.拆除()
        return 拆
    上下文.副作用(拆限额,'ui-settings-subagent: limits form subscription')
    模型=子智能体模型选择卡片控制器(上下文.configForms.get(子智能体模型选择命名空间),上下文)
    限额面=限额.注入()
    模型面=模型.注入()
    def 订适配器():
        """适配器目录失效。"""
        return 上下文.remote.$on('llm/adapters-updated',模型.刷新目录)
    上下文.副作用(订适配器,'ui-settings-subagent: adapter invalidations')
    def 订文档():
        """设置文档失效。"""
        return 上下文.remote.$on('settings/document-updated',模型.刷新目录)
    上下文.副作用(订文档,'ui-settings-subagent: settings invalidations')
    def 订重连():
        """连接换代。"""
        return 上下文.监听('connection/reset',模型.重置连接)
    上下文.副作用(订重连,'ui-settings-subagent: connection generation')
    def 拆模型():
        """拆除模型偏好。"""
        def 拆():
            """dispose。"""
            模型.拆除()
        return 拆
    上下文.副作用(拆模型,'ui-settings-subagent: model preference')
    def 挂页():
        """任一命名空间被服务时注入插件页。"""
        def 登记():
            """登记 plugins.item。"""
            def 标签():
                """页标题。"""
                return 翻译('subagentTitle')
            def 注入卡片():
                """组合限额与模型面。"""
                return 子智能体卡片面(限额面,模型面)
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'subagent',
                'order':30,
                'label':标签,
                'locale':命名空间,
                'inject':注入卡片,
            },子智能体卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        """whileServed。"""
        return 上下文.configForms.whileServed([子智能体命名空间,子智能体模型选择命名空间],挂页)
    上下文.副作用(监视,'ui-settings-subagent: page')

inject=依赖
apply=应用
