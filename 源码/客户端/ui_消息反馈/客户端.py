"""消息反馈插件的浏览器半边。

对齐上游 `ui-message-feedback/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文#词表
from .表面 import 反馈表面#按会话表面
from .反馈动作 import 消息反馈动作#赞/踩组件

__all__=['注入','应用','反馈表面','消息反馈动作','命名空间','中文','英文']#仅中文公开名

注入=['slots','remote','remote.messageFeedback','remote.sessionFeedback','locale']#依赖

def 应用(上下文):#安装消息反馈浏览器半边
    """逐条消息反馈入口、会话对话框入口及其按会话表面。"""
    def 登记词典():#登记词表
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-message-feedback: dictionaries')#登记词表
    表面表={}#会话 id → 表面

    def 表面于(会话标识):#按会话取或铸造
        """每个 Session 一个表面。"""
        if 会话标识 in 表面表:#已有
            return 表面表[会话标识]#复用
        新建=反馈表面(上下文,会话标识)#铸造
        表面表[会话标识]=新建#记入
        return 新建#返回

    def 拆除表面():#拆除全部
        """销毁表面。"""
        for 表面 in 表面表.values():#每个
            表面.拆除()#拆除
        表面表.clear()#清空
    上下文.副作用(lambda:拆除表面,'ui-message-feedback: per-session surfaces')#寿命

    def 连接重置():#重连
        """只作废已经读过的。"""
        for 表面 in 表面表.values():#每个
            if 表面.反馈.getSnapshot()['status']!='cold':#已读过
                表面.反馈.resync()#重同步
    上下文.监听('connection/reset',连接重置)#连接重置

    def 登记动作():#等助手动作槽出现再登记
        """登记赞/踩动作。"""
        def 注入面(会话标识):#按会话解析注入面
            """把表面与动词交给占用方。"""
            表面=表面于(会话标识)#取或铸造
            def 确保():#确保已读
                """ensure。"""
                return 表面.反馈.ensure()#确保
            def 当前(消息标识):#当前条目
                """current。"""
                条目=表面.反馈.getSnapshot()['items']#表
                return 条目[消息标识] if 消息标识 in 条目 else None#条目
            def 切换(消息标识,评价):#切换
                """toggle。"""
                return 表面.反馈.toggle(消息标识,评价)#切换
            def 打开对话框(消息标识):#打开
                """openDialog。"""
                表面.对话框.打开({'kind':'message','messageId':消息标识})#打开
            def 确认():#确认轻提示
                """acknowledge。"""
                表面.对话框.确认()#确认
            return {#注入面
                'hooks':{'feedback':表面.反馈},#共享视图
                'ensure':确保,#确保已读
                'current':当前,#当前条目
                'toggle':切换,#切换
                'openDialog':打开对话框,#打开对话框
                'acknowledge':确认,#确认
            }#注入结束
        return 上下文.slots.register({#登记
            'name':'conversation.chat.assistant-actions',#助手动作槽
            'id':'feedback',#条目 id
            'order':10,#顺序
            'locale':命名空间,#文案
            'inject':注入面,#注入
        },消息反馈动作)#组件
    上下文.slots.inject('conversation.chat.assistant-actions',登记动作)#等槽出现

    def 登记对话框():#等覆盖层槽出现再登记
        """登记反馈对话框。组件占位用消息反馈动作直至 FeedbackDialog 落地。"""
        def 注入面(会话标识):#按会话解析
            """对话框注入。"""
            对话框=表面于(会话标识).对话框#对话框
            return {#注入面
                'hooks':{'dialog':对话框.状态},#状态
                'edit':对话框.编辑,#编辑
                'submit':对话框.提交草稿,#提交
                'dismiss':对话框.关闭,#关闭
                'dismissToast':对话框.退役轻提示,#退役
            }#注入结束
        return 上下文.slots.register({#登记
            'name':'conversation.input.overlay',#覆盖层
            'id':'feedback-dialog',#条目 id
            'order':2,#顺序
            'locale':命名空间,#文案
            'inject':注入面,#注入
        },消息反馈动作)#组件占位
    上下文.slots.inject('conversation.input.overlay',登记对话框)#等槽出现

    def 挂命令装饰(子上下文):#命令 UI 可用时
        """裸 /feedback 打开会话对话框。"""
        def 登记装饰():#装饰
            """decorate feedback。"""
            def 跑(会话):#打开
                """打开会话级对话框。"""
                标识=会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId#会话 id
                表面于(标识).对话框.打开({'kind':'session'})#打开
            return 子上下文.commandUi.decorate({#装饰
                'name':'feedback',#命令名
                'available':lambda:True,#始终可用
                'ui':{'kind':'action','run':跑},#动作
            })#decorate 结束
        子上下文.副作用(登记装饰,'ui-message-feedback: /feedback decoration')#副作用
    上下文.依赖启动(['commandUi'],挂命令装饰)#命令 UI 门

inject=注入#框架槽
apply=应用#框架槽
