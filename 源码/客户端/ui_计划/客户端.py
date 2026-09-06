"""计划控制插件的浏览器半边。

对齐上游 `ui-plan/src/client/index.ts`。公开面仅中文名。

占据 conversation.input.plan 席位，用活动状态芯片展示。
"""
from .文案 import 命名空间,中文,英文#词表
from .计划芯片 import 计划芯片#芯片组件

__all__=['注入','应用','计划芯片','命名空间','中文','英文']#仅中文公开名

注入=['slots','remote','remote.commands','locale']#槽位、远程、commands Remote、文案

def 应用(上下文):#安装计划控制浏览器半边
    """经命令通道登记计划芯片。"""
    def 登记词表():#登记中英文案
        """把计划命名空间写进 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记词表
    上下文.副作用(登记词表,'ui-plan: dictionaries')#登记词表

    def 注入面(会话标识):#按会话解析计划芯片注入面
        """执行 /plan off 离开计划模式。commands.execute 返回任务。"""
        def 退出计划模式():#执行 /plan off
            """受理执行时为 None；否则是用户可见失败行。"""
            结果=上下文.remote.commands.execute(会话标识,'/plan off').等待()#执行
            if not 结果['ok']:#命令失败
                错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
                消息=错误['message'] if 'message' in 错误 else None#文案
                码=错误['code'] if 'code' in 错误 else None#错误码
                return str(消息)+' ('+str(码)+')'#失败行
            if 'value' not in 结果 or 结果['value'] is None:#宿主无该命令
                return 'unknown command: /plan off'#失败行
            return None#受理
        return {'exitPlanMode':退出计划模式}#注入面

    def 登记芯片():#等席位出现
        """登记计划芯片。"""
        return 上下文.slots.register({#席位登记
            'name':'conversation.input.plan',#席位槽名
            'locale':命名空间,#文案
            'inject':注入面,#注入
        },计划芯片)#计划芯片
    上下文.slots.inject('conversation.input.plan',登记芯片)#等席位出现

inject=注入#框架槽
apply=应用#框架槽
