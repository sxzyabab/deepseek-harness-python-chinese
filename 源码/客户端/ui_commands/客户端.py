"""命令界面插件浏览器半边。

对齐上游 `ui-commands/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文#词典
from .服务 import 命令界面运行时,边界加分,模糊评分,模糊候选#运行时与模糊候选
from .弹出选择视图 import 弹出选择视图#壳组件
from .弹出 import 过滤选项,弹出选择控制器#弹出
from .目录 import 命令目录#目录缓存

__all__=[#仅中文公开名
    '注入','应用','命令界面运行时','弹出选择视图','过滤选项','弹出选择控制器',
    '命令目录','边界加分','模糊评分','模糊候选','命名空间','中文','英文',
]#公开面结束

注入=['inputTriggers','sessions','remote','remote.commands','locale']#依赖

def 应用(上下文):#安装命令界面浏览器半边
    """挂服务，登记词典与 popupSelect 壳。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-commands: dictionaries')#词典
    上下文.plugin(命令界面运行时)#挂运行时
    def 挂壳(作用域):#等槽位、命令界面、会话
        """登记 conversation.input.overlay 上的 command-popup。"""
        命令=作用域.commandUi#运行时
        会话们=作用域.sessions#会话
        def 登记():#登记壳
            """弹层选择视图。"""
            def 注入面(会话标识):#按会话解析
                """交出该会话弹出控制器。"""
                作用域会话=会话们.scope(会话标识)#作用域
                if 作用域会话 is None:#无
                    raise Exception('ui-commands: session "'+str(会话标识)+'" resolved no scope')#失败
                return {'popup':命令.popupFor(作用域会话)}#注入面
            return 作用域.slots.register({#登记
                'name':'conversation.input.overlay',#叠层槽
                'id':'command-popup',#条目 id
                'order':1,#顺序
                'locale':命名空间,#词表
                'inject':注入面,#注入
            },弹出选择视图)#组件
        作用域.slots.inject('conversation.input.overlay',登记)#等槽
    上下文.inject(['slots','commandUi','sessions'],挂壳)#注入
