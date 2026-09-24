from .文案 import 命名空间,中文,英文
from .网页搜索卡片 import 网页搜索卡片
from .网页搜索卡片控制器 import 网页搜索命名空间,网页搜索卡片控制器

__all__=['依赖','应用','命名空间','中文','英文','网页搜索命名空间','网页搜索卡片控制器']

依赖=['slots','locale','remote','remote.credentials','configForms']

def 应用(上下文):
    """Host 服务 web-search-deepseek 期间，把本页登记进 plugins.item。"""
    翻译=上下文.locale.bind(命名空间)
    def 登记词典():
        """登记本页词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-settings-web-search: dictionaries')
    卡片=网页搜索卡片控制器(上下文.configForms.get(网页搜索命名空间),上下文)
    def 拆表单():
        """拆除表单订阅。"""
        def 拆():
            """dispose。"""
            卡片.拆除()
        return 拆
    上下文.副作用(拆表单,'ui-settings-web-search: form subscription')
    def 订凭据():
        """凭据引用更新时重读徽章。"""
        return 上下文.remote.$on('credentials/reference-updated',卡片.刷新凭据)
    上下文.副作用(订凭据,'ui-settings-web-search: credential invalidations')
    def 挂页():
        """命名空间被服务时注入插件页。"""
        def 登记():
            """登记 plugins.item。"""
            def 标签():
                """页标题。"""
                return 翻译('title')
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'web-search',
                'order':40,
                'label':标签,
                'locale':命名空间,
                'inject':卡片.注入,
            },网页搜索卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        """whileServed。"""
        return 上下文.configForms.whileServed([网页搜索命名空间],挂页)
    上下文.副作用(监视,'ui-settings-web-search: page')

inject=依赖
apply=应用
