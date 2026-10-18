from ....基础设施.通用工具 import 获取内部数据
from . import 文案
from . import 网页搜索卡片
from . import 网页搜索卡片控制器

__all__=['文案','网页搜索卡片','网页搜索卡片控制器','命名空间','依赖','应用']

命名空间='settings.webSearch'
依赖=['slots','locale','remote','remote.credentials','configForms']

def 应用(上下文,配置=None):
    'Host 提供 web-search-deepseek 期间，把本页登记进 plugins.item'
    def 登记词典():
        '登记本页中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-settings-web-search: dictionaries')
    卡片=网页搜索卡片控制器.网页搜索卡片控制器(
        上下文.configForms.get(网页搜索卡片控制器.网页搜索命名空间),
        上下文,
    )
    def 拆表单():
        '拆除表单订阅'
        def 拆():
            '释放控制器'
            卡片.拆除()
        return 拆
    上下文.副作用(拆表单,'ui-settings-web-search: form subscription')
    def 订凭据():
        '凭据引用更新时重读徽章'
        return getattr(上下文.remote,'$on')('credentials/reference-updated',卡片.刷新凭据)
    上下文.副作用(订凭据,'ui-settings-web-search: credential invalidations')
    def 挂页(已服务):
        '命名空间被服务时注入插件页。已服务是镜像里当前有的命名空间，调用方已经确认本页在其中'
        def 登记():
            '登记 plugins.item'
            def 标签():
                '页标题。用中文表原文，是网页搜索'
                return 文案.中文['title']
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'web-search',
                'order':20,
                'label':标签,
                'locale':命名空间,
                'inject':卡片.注入,
            },网页搜索卡片.网页搜索卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        '命名空间出现在镜像里才挂上本页'
        return 上下文.configForms.在已提供期间(
            [网页搜索卡片控制器.网页搜索命名空间],
            挂页,
        )
    上下文.副作用(监视,'ui-settings-web-search: page')

inject=依赖
apply=应用
