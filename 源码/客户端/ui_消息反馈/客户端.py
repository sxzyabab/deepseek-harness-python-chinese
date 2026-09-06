"""消息反馈插件的浏览器半边。

对齐上游 `ui-message-feedback/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文#词表
from .控制器 import 消息反馈控制器#按会话控制器
from .反馈动作 import 消息反馈动作#赞/踩组件

__all__=['注入','应用','消息反馈控制器','消息反馈动作','命名空间','中文','英文']#仅中文公开名

注入=['slots','remote','remote.messageFeedback','locale']#槽位、远程、messageFeedback、文案

def 应用(上下文):#安装消息反馈浏览器半边
    """逐条消息的反馈入口及其按会话的对象层。"""
    def 登记词典():#登记词表
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-message-feedback: dictionaries')#登记词表
    控制器表={}#会话 id → 控制器

    def 控制器于(会话标识):#按会话取或铸造
        """每个 Session 一个控制器。"""
        if 会话标识 in 控制器表:#已有
            return 控制器表[会话标识]#复用
        新建=消息反馈控制器(上下文.remote.messageFeedback,会话标识)#铸造
        控制器表[会话标识]=新建#记入
        return 新建#返回

    def 连接重置():#重连
        """只作废已经读过的。"""
        for 控制器 in 控制器表.values():#每个
            if 控制器.getSnapshot()['status']!='cold':#已读过
                控制器.resync()#重同步
    上下文.监听('connection/reset',连接重置)#连接重置

    def 登记动作():#等助手动作槽出现再登记
        """登记赞/踩动作。"""
        def 注入面(会话标识):#按会话解析注入面
            """把控制器与动词交给占用方。"""
            控制器=控制器于(会话标识)#取或铸造
            def 确保():#确保已读
                """ensure。"""
                return 控制器.ensure()#确保
            def 评分(消息标识,评价,附注=None):#评分
                """rate。"""
                return 控制器.rate(消息标识,评价,附注)#评分
            def 切换(消息标识,评价):#切换
                """toggle。"""
                return 控制器.toggle(消息标识,评价)#切换
            def 清说明(消息标识):#清说明
                """clearNote。"""
                return 控制器.clearNote(消息标识)#清
            def 清反馈(消息标识):#清反馈
                """clear。"""
                return 控制器.clear(消息标识)#清
            return {#注入面
                'hooks':{'feedback':控制器},#共享视图
                'ensure':确保,#确保已读
                'rate':评分,#评分
                'toggle':切换,#切换
                'clearNote':清说明,#清说明
                'clear':清反馈,#清反馈
            }#注入结束
        拆除=上下文.slots.register({#登记
            'name':'conversation.chat.assistant-actions',#助手动作槽
            'id':'feedback',#条目 id
            'order':10,#顺序
            'locale':命名空间,#文案
            'inject':注入面,#注入
        },消息反馈动作)#组件
        def 全拆除():#拆除槽位与控制器
            """撤销登记并拆除控制器。"""
            拆除()#撤销
            for 控制器 in 控制器表.values():#每个
                控制器.dispose()#拆除
            控制器表.clear()#清空
        return 全拆除#拆除器
    上下文.slots.inject('conversation.chat.assistant-actions',登记动作)#等槽出现

inject=注入#框架槽
apply=应用#框架槽
