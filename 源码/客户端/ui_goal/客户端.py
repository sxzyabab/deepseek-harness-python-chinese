"""目标界面插件的浏览器半边。



对齐上游 `ui-goal/src/client/index.ts`。公开面仅中文名。

conversation.input.dock 条上的 GoalBar 条目；投影模式，不拥有 store。

"""

from cordis.工具 import 是否thenable#可等待判定

from .文案 import 命名空间,中文,英文#词表

from .槽位 import 无当前目标结果#失败结果

from .命令输入 import 目标命令输入定义#节点定义

from .命令输入视图 import 目标命令输入视图#聊天节点视图

from .目标条 import 目标坞#坞组件



__all__=['注入','应用','目标坞','目标命令输入视图','目标命令输入定义','命名空间','中文','英文']#仅中文公开名



注入=['slots','sessions','remote','remote.goals','locale','conversationEvents']#槽位、会话、远程、goals、文案、会话事件



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺席#缺席

    return getattr(对象,键,缺省)#属性



def 解开(值):#承诺则等待否则原样

    """承诺则等待，否则原样返回。"""

    if 是否thenable(值):#可等待

        return 值.等待()#等待

    return 值#同步



def 应用(上下文):#安装目标界面浏览器半边

    """带变更动词的 GoalBar 坞条目。"""

    上下文.conversationEvents.register(目标命令输入定义)#登记命令输入会话节点定义

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-goal: dictionaries')#登记词表



    上下文.slots.inject('conversation.chat.node',lambda:上下文.slots.register({#等聊天节点槽

        'name':'conversation.chat.node',#聊天节点槽名

        'key':'command-input',#命令输入条目键

        'locale':命名空间,#文案

    },目标命令输入视图))#命令输入视图



    会话服务=上下文.sessions#会话服务



    def 引用于(会话标识):#按会话取出当前目标的 CAS ref

        """没有投影则没有 ref。"""

        绑定=会话服务.binding(会话标识) if 会话服务 is not None else None#绑定

        会话=取字段(绑定,'session') if 绑定 is not None else None#会话

        投影表=取字段(会话,'projections') if 会话 is not None else None#投影表

        面=投影表.faceOf('goal') if 投影表 is not None and hasattr(投影表,'faceOf') else None#goal 面

        投影=面.getSnapshot() if 面 is not None and hasattr(面,'getSnapshot') else None#快照

        if 投影 is None:#没有投影

            return None#无 ref

        目标=取字段(投影,'goal')#目标

        if 目标 is None:#无目标

            return None#无 ref

        return {'id':取字段(目标,'id'),'revision':取字段(目标,'revision')}#CAS ref



    def 注入面(会话标识):#按会话解析 GoalBar 变更动词

        """CAS ref 在调用时读取。"""

        def 编辑(陈述):#编辑目标陈述

            """无当前目标则失败结果。"""

            引用=引用于(会话标识)#CAS ref

            if 引用 is None:#无

                return 无当前目标结果#失败

            return 解开(上下文.remote.goals.edit(会话标识,引用,{'objective':陈述}))#编辑

        def 暂停():#暂停目标

            """无当前目标则失败结果。"""

            引用=引用于(会话标识)#CAS ref

            if 引用 is None:#无

                return 无当前目标结果#失败

            return 解开(上下文.remote.goals.pause(会话标识,引用))#暂停

        def 恢复():#恢复目标

            """无当前目标则失败结果。"""

            引用=引用于(会话标识)#CAS ref

            if 引用 is None:#无

                return 无当前目标结果#失败

            return 解开(上下文.remote.goals.resume(会话标识,引用))#恢复

        def 清除():#清除目标

            """无当前目标则失败结果。"""

            引用=引用于(会话标识)#CAS ref

            if 引用 is None:#无

                return 无当前目标结果#失败

            return 解开(上下文.remote.goals.clear(会话标识,引用))#清除

        return {'onEdit':编辑,'onPause':暂停,'onResume':恢复,'onClear':清除}#动词面



    上下文.slots.inject('conversation.input.dock',lambda:上下文.slots.register({#等输入坞槽

        'name':'conversation.input.dock',#输入坞槽名

        'id':'goal',#条目 id

        'order':10,#坞条顺序

        'locale':命名空间,#文案

        'inject':注入面,#注入

    },目标坞))#GoalBar 坞组件


