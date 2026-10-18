from . import 文案
from . import 终端卡片
from . import 终端卡片控制器

__all__=['文案','终端卡片','终端卡片控制器','命名空间','依赖','应用']

命名空间='settings.shell'
依赖=['slots','locale','configForms']

def 应用(上下文,配置=None):
    'Host 服务 bash-sandbox 或 pwsh-sandbox 期间，把本页登记进 plugins.item'
    def 登记词典():
        '登记本页中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-settings-shell: dictionaries')
    bash卡=终端卡片控制器.终端卡片控制器(上下文.configForms.get(终端卡片控制器.bash命名空间))
    pwsh卡=终端卡片控制器.终端卡片控制器(上下文.configForms.get(终端卡片控制器.pwsh命名空间))
    def 拆表单():
        '拆除两条表单订阅'
        def 拆():
            '释放两条控制器'
            bash卡.拆除()
            pwsh卡.拆除()
        return 拆
    上下文.副作用(拆表单,'ui-settings-shell: form subscriptions')
    def 挂页(已服务):
        '任一执行器在服务里时注入插件页。已服务是镜像里当前有的命名空间'
        def 登记():
            '登记 plugins.item'
            def 标签():
                '页标题。用中文表原文，是终端'
                return 文案.中文['title']
            def 注入():
                '当前服务里有 PowerShell 就用它，否则用 POSIX。每次注入时再看已服务'
                选=pwsh卡 if 终端卡片控制器.pwsh命名空间 in 已服务 else bash卡
                return 选.注入()
            return 上下文.slots.register({
                'name':'plugins.item',
                'id':'shell',
                'order':40,
                'label':标签,
                'locale':命名空间,
                'inject':注入,
            },终端卡片.终端卡片)
        return 上下文.slots.inject('plugins.item',登记)
    def 监视():
        '任一执行器命名空间出现在镜像里才挂上本页'
        return 上下文.configForms.在已提供期间(
            [终端卡片控制器.bash命名空间,终端卡片控制器.pwsh命名空间],
            挂页,
        )
    上下文.副作用(监视,'ui-settings-shell: page')

inject=依赖
apply=应用
