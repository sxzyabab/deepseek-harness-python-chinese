"""权限预设插件的浏览器半边。



对齐上游 `ui-permission-presets/src/client/index.ts`。公开面仅中文名。

挂在宿主 /permission 命令上的 popupSelect 装饰 + 通用设置行。

"""

from .文案 import 设置中文,设置英文,访问中文,访问英文#词表

from .展示 import 显示权限预设,完全访问预设#展示层

from .设置仓库 import 权限设置命名空间,权限预设设置控制器,已加载则刷新权限#设置仓库

from .权限行 import 权限行#通用设置行



__all__=['注入','应用','权限行','完全访问预设','显示权限预设']#仅中文公开名



注入=['commandUi','sessions','slots','locale','connection','remote']#命令 UI、会话、槽位、文案、连接、远程

访问命名空间='permission.access'#完全访问确认词表命名空间



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



def 投影于(会话):#会话 → 权限投影

    """读 permissions 投影；无会话则为 None。"""

    if 会话 is None:#无

        return None#缺席

    投影=取字段(会话,'projections')#投影面

    if 投影 is None:#无

        return None#缺席

    面=投影.faceOf('permissions') if hasattr(投影,'faceOf') else None#权限面

    if 面 is None:#无

        return None#缺席

    return 面.getSnapshot()#快照



def 选项于(值,翻译):#投影 → 弹出选项

    """custom 只是展示态，永远不是切换目标。"""

    结果=[]#选项

    for 选项 in 取字段(值,'options') or []:#宿主算出的预设

        if 取字段(选项,'value')=='custom':#仅展示

            continue#丢掉

        行={#弹出行

            'id':取字段(选项,'value'),#预设键

            'label':显示权限预设(取字段(选项,'value'),取字段(选项,'name')),#显示名

        }#行

        if 取字段(选项,'description') is not None:#有描述

            行['detail']=取字段(选项,'description')#detail

        if 取字段(选项,'value')==取字段(值,'currentValue'):#当前值

            行['active']=True#标 active

        if 取字段(选项,'value')==完全访问预设:#完全访问行

            行['confirmation']={#风险确认

                'title':翻译('confirm.title'),#标题

                'description':翻译('confirm.description'),#说明

                'acknowledgeLabel':翻译('confirm.acknowledge'),#知晓

                'cancelLabel':翻译('confirm.cancel'),#取消

                'confirmLabel':翻译('confirm.enable'),#启用

            }#确认结束

        结果.append(行)#加入

    return 结果#选项



def 应用(上下文):#安装权限预设浏览器半边

    """在 permissions 投影上登记 /permission 弹出选择器，并登记通用设置行。"""

    命令=上下文.get('commandUi')#命令 UI 约定

    会话服务=上下文.sessions#会话服务



    def 登记确认词表():#登记完全访问确认词表

        """中英文确认词表。"""

        拆除们=[#disposer

            上下文.locale.register(访问命名空间,'zh',{#中文

                'confirm.title':访问中文['confirm.title'],#标题

                'confirm.description':访问中文['confirm.description'],#说明

                'confirm.acknowledge':访问中文['confirm.acknowledge'],#知晓

                'confirm.cancel':访问中文['confirm.cancel'],#取消

                'confirm.enable':访问中文['confirm.enable'],#启用

            }),#中文结束

            上下文.locale.register(访问命名空间,'en',{#英文

                'confirm.title':访问英文['confirm.title'],#标题

                'confirm.description':访问英文['confirm.description'],#说明

                'confirm.acknowledge':访问英文['confirm.acknowledge'],#知晓

                'confirm.cancel':访问英文['confirm.cancel'],#取消

                'confirm.enable':访问英文['confirm.enable'],#启用

            }),#英文结束

        ]#拆除们结束

        def 拆除():#拆除

            """逐个取消。"""

            for 拆 in 拆除们:#逐个

                拆()#拆除

        return 拆除#拆除器

    上下文.effect(登记确认词表,'ui-permission: Full access confirmation dictionaries')#确认词表

    翻译=上下文.locale.bind(访问命名空间)#绑定确认词表

    上下文.effect(lambda:上下文.locale.register('settings.permission',{'zh':设置中文,'en':设置英文}),'ui-permission: settings row dictionaries')#设置行词表



    连接=上下文.get('connection')#连接句柄

    控制器=权限预设设置控制器(取字段(连接,'api'))#设置控制器



    def 注入面():#通用设置行注入面

        """把设置 store 交给行。"""

        return {#注入

            'hooks':{'permission':控制器.store},#快照仓库

            'load':lambda:控制器.load(),#加载

            'select':lambda 预设:控制器.select(预设),#选定

        }#注入结束



    def 设置失效():#设置失效订阅

        """外部改设置或重连都可能动这一行。"""

        def 刷新():#已加载过才刷新

            """刷新。"""

            已加载则刷新权限(控制器)#刷新

        拆除们=[#两路

            上下文.remote.$on('settings/document-updated',lambda 命名空间:(刷新() if 命名空间==权限设置命名空间 else None)),#文档更新

            上下文.on('connection/reset',lambda:刷新()),#重连

        ]#拆除们

        def 拆除():#拆除

            """丢掉控制器并退订。"""

            控制器.dispose()#控制器

            for 拆 in 拆除们:#订阅

                拆()#退订

        return 拆除#拆除器

    上下文.effect(设置失效,'ui-permission: settings invalidations')#失效



    上下文.slots.inject('settings.general.item',lambda:上下文.slots.register({#等通用设置条目槽

        'name':'settings.general.item',#槽名

        'id':'permission',#条目 id

        'order':-20,#较前

        'locale':'settings.permission',#文案

        'inject':注入面,#注入

    },权限行))#行组件



    def 会话面(会话):#从输入触发会话拿到运行时会话面

        """绑定存在才有会话。"""

        绑定=会话服务.binding(取字段(会话,'sessionId'))#绑定

        return 取字段(绑定,'session') if 绑定 is not None else None#会话面



    def 装饰命令():#给宿主 /permission 挂弹出选择装饰

        """登记 /permission 弹出选择。"""

        def 可用(会话):#有投影才露出

            """可用性。"""

            return 投影于(会话面(会话)) is not None#有投影

        def 选项(会话):#加载可选行

            """投影展平为行。"""

            值=投影于(会话面(会话))#投影

            if 值 is None:#无

                raise Exception('permission presets are not available on this host')#失败

            return 选项于(值,翻译)#展平

        def 选定(选项行,会话):#点中一行

            """走同一命令行。"""

            活=会话面(会话)#运行时会话面

            if 活 is None:#尚未物化

                raise Exception('this session is not materialized yet')#失败

            结果=活.command('/permission '+取字段(选项行,'id'))#提交

            if hasattr(结果,'等待'):#承诺

                结果=结果.等待()#等待

            if not 取字段(结果,'ok'):#命令失败

                错误=取字段(结果,'error') or {}#错误

                raise Exception('permission switch failed: '+str(取字段(错误,'code'))+': '+str(取字段(错误,'message')))#失败

            if not 取字段(取字段(结果,'value'),'matched'):#宿主无该命令

                raise Exception('the host offers no /permission command')#失败

        return 命令.decorate({#装饰

            'name':'permission',#命令名

            'available':可用,#可用性

            'ui':{'kind':'popupSelect','options':选项,'onSelect':选定},#UI

        })#decorate 结束

    上下文.effect(装饰命令,'ui-permission: /permission decoration')#装饰生命周期


