from ....预设.智能体预设注册表.展示 import 预设展示文本
from ...ui_智能体预设.客户端.文案 import 取中文
from . import 文案
from . import 清单页签
from .文案 import 中文,英文

__all__=['文案','清单页签','命名空间','依赖','应用']

命名空间='settings.pluginInventory'
依赖=['slots','locale','remote','remote.pluginInventory','modules']

def 应用(上下文,配置=None):
    '把只读插件清单页签登记进插件设置'
    def 登记词典():
        '登记中英文案表。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-settings-plugin-inventory: dictionaries')
    def 列表():
        '读取当前宿主插件清单。失败抛出上游那句错误'
        结果=上下文.remote.pluginInventory.list()
        if 结果['ok'] is not True:
            错误=结果['error']
            raise Exception('pluginInventory.list failed: '+str(错误['code'])+': '+str(错误['message']))
        return 结果['value']
    def 预设名(预设):
        '出厂预设走中文表原文，自写名称保持元数据'
        return 预设展示文本(预设,取中文)['name']
    def 重试本页():
        '重试本页模块图，不改宿主组合'
        try:
            上下文.modules.entries.retry()
        except Exception as 错误:
            上下文.日志.错误(错误)
    def 注入面():
        '清单、预设名、包文案和本页同步'
        return {
            'list':列表,
            'presetName':预设名,
            'resolveText':上下文.locale.resolveText,
            'hooks':{'clientSync':上下文.modules.entries.state},
            'retryClient':重试本页,
        }
    def 页签标签():
        '插件列表'
        return 中文['tab']
    def 登记页签():
        '登记 settings.plugins.tab 的全部清单'
        return 上下文.slots.register({
            'name':'settings.plugins.tab',
            'id':'all',
            'order':10,
            'label':页签标签,
            'locale':命名空间,
            'inject':注入面,
        },清单页签.插件清单页签)
    上下文.slots.inject('settings.plugins.tab',登记页签)

inject=依赖
apply=应用
