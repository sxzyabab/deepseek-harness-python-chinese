from ....基础设施.通用工具 import 获取内部数据
from . import 文案
from . import 子智能体卡片
from . import 子智能体卡片控制器
from . import 子智能体限额卡片控制器
from . import 子智能体限额字段
from . import 子智能体模型选择卡片控制器
from . import 子智能体模型选择字段

__all__=[
    '文案','子智能体卡片','子智能体卡片控制器',
    '子智能体限额卡片控制器','子智能体限额字段',
    '子智能体模型选择卡片控制器','子智能体模型选择字段',
    '命名空间','子智能体命名空间','依赖','应用',
]

命名空间='settings.subagent'
子智能体命名空间='subagent'
依赖=['slots','locale','remote','remote.session','configForms']

def 应用(上下文,配置=None):
    '限额或模型选择任一命名空间在服务时，把本页登记进 plugins.item'
    def 登记词典():
        '登记本页中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-settings-subagent: dictionaries')
    限额=子智能体限额卡片控制器.子智能体限额卡片控制器(
        上下文.configForms.get(子智能体命名空间),
    )
    def 拆限额():
        '拆除限额表单订阅'
        def 拆():
            '释放限额控制器'
            限额.拆除()
        return 拆
    上下文.副作用(拆限额,'ui-settings-subagent: limits form subscription')
    模型=子智能体模型选择卡片控制器.子智能体模型选择卡片控制器(
        上下文.configForms.get(子智能体模型选择卡片控制器.子智能体模型选择命名空间),
        上下文,
    )
    限额面=限额.注入()
    模型面=模型.注入()
    def 订适配器():
        '适配器目录失效后重拉候选'
        def 适配器变(*位置参数):
            '忽略事件载荷'
            模型.刷新目录()
        return getattr(上下文.remote,'$on')('llm/adapters-updated',适配器变)
    上下文.副作用(订适配器,'ui-settings-subagent: adapter invalidations')
    def 订文档():
        '设置文档失效后重拉候选'
        def 文档变(*位置参数):
            '忽略事件载荷'
            模型.刷新目录()
        return getattr(上下文.remote,'$on')('settings/document-updated',文档变)
    上下文.副作用(订文档,'ui-settings-subagent: settings invalidations')
    def 订重连():
        '连接换代后丢掉草稿再拉目录'
        def 连接重设(*位置参数):
            '忽略事件载荷'
            模型.重置连接()
        return 上下文.监听('connection/reset',连接重设)
    上下文.副作用(订重连,'ui-settings-subagent: connection generation')
    def 拆模型():
        '拆除模型偏好订阅'
        def 拆():
            '作废在途结算并退订'
            模型.拆除()
        return 拆
    上下文.副作用(拆模型,'ui-settings-subagent: model preference')
    def 挂页(已服务):
        '任一命名空间出现在镜像里时注入插件页。已服务由调用方传入，这里不再筛一遍'
        def 登记():
            '登记 plugins.item'
            def 标签():
                '页标题。用中文表原文，是子智能体'
                return 文案.中文['subagentTitle']
            def 注入卡片():
                '限额与模型合成一次保存，各自仍走自己的修订栅栏'
                def 保存():
                    '两节都合法且有改动时，分别交给各自的命名空间'
                    限额态=限额面['hooks']['subagentLimitsCard'].getSnapshot()
                    模型态=模型面['hooks']['subagentModelSelectionCard'].getSnapshot()
                    状态=子智能体卡片控制器.子智能体卡片外壳(限额态,模型态)
                    if (
                        not 状态['available'] or not 状态['writable'] or not 状态['dirty']
                        or 状态['invalid'] or 状态['saving']
                    ):
                        return
                    if 模型态['available'] and 模型态['dirty']:
                        模型面['save']()
                    if 限额态['available'] and 限额态['dirty']:
                        限额面['save']()
                def 丢弃():
                    '保存进行中时两节都不丢'
                    if 子智能体卡片控制器.子智能体卡片外壳(
                        限额面['hooks']['subagentLimitsCard'].getSnapshot(),
                        模型面['hooks']['subagentModelSelectionCard'].getSnapshot(),
                    )['saving']:
                        return
                    限额面['discard']()
                    模型面['discard']()
                def 切换开启(*位置参数):
                    '开关会传来下一态。控制器自己翻转，不采用这个值'
                    模型面['toggleEnabled']()
                return {
                    'hooks':{**限额面['hooks'],**模型面['hooks']},
                    'editLimit':限额面['edit'],
                    'resetLimit':限额面['resetField'],
                    'toggleEnabled':切换开启,
                    'toggleModel':模型面['toggleModel'],
                    'retryCatalog':模型面['retryCatalog'],
                    'save':保存,
                    'discard':丢弃,
                }
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'subagent',
                'order':10,
                'label':标签,
                'locale':命名空间,
                'inject':注入卡片,
            },子智能体卡片.子智能体卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        '限额或模型选择命名空间出现在镜像里才挂上本页'
        return 上下文.configForms.在已提供期间(
            [子智能体命名空间,子智能体模型选择卡片控制器.子智能体模型选择命名空间],
            挂页,
        )
    上下文.副作用(监视,'ui-settings-subagent: page')

inject=依赖
apply=应用
