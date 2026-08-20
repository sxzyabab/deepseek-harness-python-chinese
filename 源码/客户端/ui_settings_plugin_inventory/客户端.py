"""只读宿主插件清单的浏览器半边。



对齐上游 `ui-settings-plugin-inventory/src/client/index.ts`。公开面仅中文名。

把清单页签登记进 Web 设置。

"""

from cordis.工具 import 是否thenable#可等待判定

from .文案 import 命名空间,中文,英文#词表

from .清单页签 import 插件清单页签#页签组件



__all__=['注入','应用','插件清单页签','命名空间','中文','英文']#仅中文公开名



注入=['slots','locale','remote','remote.pluginInventory']#槽位、文案、远程、清单远程面



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



def 解开(值):#承诺则等待否则原样

    """承诺则等待，否则原样返回。"""

    if 是否thenable(值):#可等待

        return 值.等待()#等待

    return 值#同步



def 应用(上下文):#安装只读清单页签

    """把惰性清单页签贡献给插件设置分区。"""

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-settings-plugin-inventory: dictionaries')#登记词表

    翻译=上下文.locale.bind(命名空间)#绑定本插件词表



    def 列表():#拉取当前宿主清单快照

        """调用清单远程面；失败抛错。"""

        结果=解开(上下文.remote.pluginInventory.list())#远程 list

        if not 取字段(结果,'ok'):#业务失败

            错误=取字段(结果,'error') or {}#错误

            raise Exception(f"pluginInventory.list failed: {取字段(错误,'code')}: {取字段(错误,'message')}")#诊断

        return 取字段(结果,'value')#快照



    def 注入面():#页签注入面

        """只暴露 list。"""

        return {'list':列表}#注入



    上下文.slots.inject('settings.plugins.tab',lambda:上下文.slots.register({#等插件页签槽出现

        'name':'settings.plugins.tab',#插件页签槽名

        'id':'all',#全部清单页签 id

        'order':10,#排在可配置页签之后

        'label':lambda:翻译('tab'),#页签标签

        'locale':命名空间,#文案

        'inject':注入面,#注入

    },插件清单页签))#页签组件


