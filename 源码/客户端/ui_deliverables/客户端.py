"""产出物插件的浏览器半边。



对齐上游 `ui-deliverables/src/client/index.ts`。公开面仅中文名。

把产出文件行登记进聊天视图的回合尾链，并提供 chatFileMentions 服务。

"""

from .文案 import 命名空间,中文,英文#词表

from .回合产出 import 交付物定义,选出产出文件,产出文件提及,收口产出#节点与选取

from .产出文件 import 产出文件行#产出文件行组件



__all__=['注入','应用','产出文件行','收口产出','选出产出文件','交付物定义','命名空间','中文','英文']#仅中文公开名



注入=['slots','locale','conversationEvents','connection']#槽位、文案、会话事件、连接



def 应用(上下文):#安装产出物浏览器半边

    """登记词表与回合尾条目。"""

    连接=上下文.get('connection')#取出连接句柄

    上下文.conversationEvents.register(交付物定义)#登记产出物会话节点定义

    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-deliverables: dictionaries')#登记词表



    上下文.slots.inject(#等回合尾槽出现再登记

        'conversation.chat.turnTail',#回合尾槽

        lambda:上下文.slots.register({#登记产出文件行

            'name':'conversation.chat.turnTail',#回合尾槽名

            'select':选出产出文件,#选出本回合产出文件

            'locale':命名空间,#文案

            'inject':lambda:{#注入回环判定与宿主描述

                'isLoopback':连接.isLoopback,#是否回环连接

                'hooks':{'hostDescription':连接.hostDescription},#宿主描述钩子

            },#注入结束

        },产出文件行),#产出文件行组件

    )#结束 turnTail 注入



    翻译=上下文.locale.bind(命名空间)#绑定本插件词表



    def 收口提及(所有者):#收口散文里的产出文件提及

        """与回合尾行同一套认领测试。"""

        路径表=选出产出文件(所有者)#选出本回合产出路径

        if 路径表 is None:#没有产出

            return None#不提供提及

        return 产出文件提及(路径表,所有者.openFile,lambda 路径:翻译('produced.open',{'name':路径}))#匹配提及



    上下文.provide('chatFileMentions',{'forClosing':收口提及})#提供收口散文提及服务


