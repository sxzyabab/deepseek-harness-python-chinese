"""计划控制插件的浏览器半边。



对齐上游 `ui-plan/src/client/index.ts`。公开面仅中文名。

占据 conversation.input.plan 席位，用活动状态芯片展示。

"""

from cordis.工具 import 是否thenable#可等待判定

from .文案 import 命名空间,中文,英文#词表

from .计划芯片 import 计划芯片#芯片组件



__all__=['注入','应用','计划芯片','命名空间','中文','英文']#仅中文公开名



注入=['slots','remote','remote.commands','locale']#槽位、远程、commands Remote、文案



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



def 应用(上下文):#安装计划控制浏览器半边

    """经命令通道登记计划芯片。"""

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-plan: dictionaries')#登记词表



    def 注入面(会话标识):#按会话解析计划芯片注入面

        """执行 /plan off 离开计划模式。"""

        def 退出计划模式():#执行 /plan off

            """受理执行时为 None；否则是用户可见失败行。"""

            结果=解开(上下文.remote.commands.execute(会话标识,'/plan off'))#执行

            if not 取字段(结果,'ok'):#命令失败

                错误=取字段(结果,'error') or {}#错误

                return str(取字段(错误,'message'))+' ('+str(取字段(错误,'code'))+')'#失败行

            if 取字段(结果,'value') is None:#宿主无该命令

                return 'unknown command: /plan off'#失败行

            return None#受理

        return {'exitPlanMode':退出计划模式}#注入面



    上下文.slots.inject('conversation.input.plan',lambda:上下文.slots.register({#等席位出现

        'name':'conversation.input.plan',#席位槽名

        'locale':命名空间,#文案

        'inject':注入面,#注入

    },计划芯片))#计划芯片


