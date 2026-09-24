from .文案 import 命名空间,中文,英文
from .终端卡片 import 终端卡片
from .终端卡片控制器 import bash命名空间,pwsh命名空间,终端卡片控制器

__all__=['依赖','应用','命名空间','中文','英文','bash命名空间','pwsh命名空间','终端卡片控制器']

依赖=['slots','locale','configForms']

def 应用(上下文):
    """Host 服务 bash-sandbox 或 pwsh-sandbox 期间，把本页登记进 plugins.item。"""
    翻译=上下文.locale.bind(命名空间)
    def 登记词典():
        """登记本页词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-settings-shell: dictionaries')
    bash=终端卡片控制器(上下文.configForms.get(bash命名空间))
    pwsh=终端卡片控制器(上下文.configForms.get(pwsh命名空间))
    def 拆表单():
        """拆除两条表单订阅。"""
        def 拆():
            """dispose。"""
            bash.拆除()
            pwsh.拆除()
        return 拆
    上下文.副作用(拆表单,'ui-settings-shell: form subscriptions')
    def 挂页(已服务):
        """按当前平台已服务的执行器注入插件页。"""
        def 登记():
            """登记 plugins.item。"""
            def 标签():
                """页标题。"""
                return 翻译('title')
            选=pwsh if pwsh命名空间 in 已服务 else bash
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'shell',
                'order':10,
                'label':标签,
                'locale':命名空间,
                'inject':选.注入,
            },终端卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        """whileServed。"""
        return 上下文.configForms.whileServed([bash命名空间,pwsh命名空间],挂页)
    上下文.副作用(监视,'ui-settings-shell: page')

inject=依赖
apply=应用
