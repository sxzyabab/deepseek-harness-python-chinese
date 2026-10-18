from . import 文案
from . import 智能体循环卡片
from . import 智能体循环卡片控制器

__all__=['文案','智能体循环卡片','智能体循环卡片控制器','命名空间','依赖','应用']

命名空间='settings.agentLoop'
依赖=['slots','locale','configForms']

def 应用(上下文,配置=None):
    'Host 服务 agent-loop 命名空间期间，把本页登记进 plugins.item'
    def 登记词典():
        '登记本页中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-settings-agent-loop: dictionaries')
    卡片=智能体循环卡片控制器.智能体循环卡片控制器(
        上下文.configForms.get(智能体循环卡片控制器.智能体循环命名空间),
    )
    def 拆表单():
        '拆除表单订阅'
        def 拆():
            '释放控制器'
            卡片.拆除()
        return 拆
    上下文.副作用(拆表单,'ui-settings-agent-loop: form subscription')
    def 挂页(已服务):
        '命名空间被服务时注入插件页。已服务是镜像里当前有的命名空间，调用方已经确认本页在其中'
        def 登记():
            '登记 plugins.item'
            def 标签():
                '页标题。用中文表原文，是 Agent 循环'
                return 文案.中文['title']
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'agent-loop',
                'order':30,
                'label':标签,
                'locale':命名空间,
                'inject':卡片.注入,
            },智能体循环卡片.智能体循环卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        'agent-loop 出现在镜像里才挂上本页'
        return 上下文.configForms.在已提供期间(
            [智能体循环卡片控制器.智能体循环命名空间],
            挂页,
        )
    上下文.副作用(监视,'ui-settings-agent-loop: page')

inject=依赖
apply=应用
