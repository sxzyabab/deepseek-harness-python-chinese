'消息反馈的浏览器半边：赞踩、对话框、feedbackUi 和 /feedback'
from . import 文案
from . import 槽位
from . import 控制器
from . import 对话框
from . import 表面
from . import 反馈动作
from . import 反馈对话框

__all__=[
    '文案',
    '槽位',
    '控制器',
    '对话框',
    '表面',
    '反馈动作',
    '反馈对话框',
    '命名空间',
    '依赖',
    '应用',
]

命名空间='feedback'
依赖=['slots','remote','remote.messageFeedback','remote.sessionFeedback','locale']

def 应用(上下文,配置=None):
    '登记文案、按会话的表面、两个槽、feedbackUi，以及 /feedback 装饰'
    def 登记词典():
        '登记本插件中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-message-feedback: dictionaries')
    表面表={}
    def 表面于(会话标识):
        '每场会话一个表面。没有就现造'
        已有=表面表.get(会话标识)
        if 已有 is None:
            已有=表面.反馈表面(上下文,会话标识)
            表面表[会话标识]=已有
        return 已有
    def 拆除表面():
        '卸下插件时拆掉每场会话的表面'
        for 一项 in 表面表.values():
            一项.拆除()
        表面表.clear()
    def 登记表面寿命():
        '把拆表面交给这条副作用'
        return 拆除表面
    上下文.副作用(登记表面寿命,'ui-message-feedback: per-session surfaces')
    def 打开会话(会话标识):
        '打开这一场的反馈草稿，不写入反馈'
        表面于(会话标识).对话框.打开({'kind':'session'})
    反馈界面={'openSession':打开会话}
    上下文.提供服务('feedbackUi',反馈界面)
    def 连接重置():
        '重连只作废已经读过的。冷的会话继续冷着，直到有人来要'
        for 一项 in 表面表.values():
            if 一项.反馈.getSnapshot()['status']!='cold':
                一项.反馈.重同步()
    上下文.监听('connection/reset',连接重置)
    def 登记动作():
        '等助手动作槽出现再登记赞和踩'
        def 注入面(会话标识):
            '把这一场的反馈视图和动词交给动作条'
            一场=表面于(会话标识)
            def 确保():
                '第一次交互时加载列表'
                return 一场.反馈.确保()
            def 当前(消息标识):
                '控制器上次看到的这一条'
                表=一场.反馈.getSnapshot()['items']
                if 消息标识 in 表:
                    return 表[消息标识]
                return None
            def 撤回(消息标识,评价):
                '评分仍匹配才删除'
                return 一场.反馈.撤回(消息标识,评价)
            def 打开对话框(消息标识,评价):
                '按这条消息和这一档评分打开草稿'
                一场.对话框.打开({
                    'kind':'message',
                    'messageId':消息标识,
                    'rating':评价,
                })
            return {
                'hooks':{'feedback':一场.反馈},
                'ensure':确保,
                'current':当前,
                'retract':撤回,
                'openDialog':打开对话框,
            }
        return 上下文.slots.register({
            'name':'conversation.chat.assistant-actions',
            'id':'feedback',
            'order':10,
            'locale':命名空间,
            'inject':注入面,
        },反馈动作.消息反馈动作)
    上下文.slots.inject('conversation.chat.assistant-actions',登记动作)
    def 登记对话框():
        '等输入覆盖层出现再登记反馈对话框'
        def 注入面(会话标识):
            '把这一场的对话框状态和动词交出去'
            对话框控制器=表面于(会话标识).对话框
            return {
                'hooks':{'dialog':对话框控制器.状态},
                'edit':对话框控制器.编辑,
                'submit':对话框控制器.提交草稿,
                'dismiss':对话框控制器.关闭,
                'dismissFailure':对话框控制器.关掉失败,
                'dismissToast':对话框控制器.退役轻提示,
            }
        return 上下文.slots.register({
            'name':'conversation.input.overlay',
            'id':'feedback-dialog',
            'order':2,
            'locale':命名空间,
            'inject':注入面,
        },反馈对话框.反馈对话框)
    上下文.slots.inject('conversation.input.overlay',登记对话框)
    def 挂命令(子上下文):
        '命令界面就绪后，裸 /feedback 打开对话框'
        def 登记装饰():
            '挂上 feedback 装饰'
            def 始终可用(会话):
                '菜单和撰写器里这条命令始终可点'
                return True
            def 执行打开(会话):
                '打开这一场的反馈草稿'
                if isinstance(会话,dict):
                    标识=会话['sessionId']
                else:
                    标识=会话.sessionId
                反馈界面['openSession'](标识)
            return 子上下文.commandUi.decorate({
                'name':'feedback',
                'available':始终可用,
                'ui':{'kind':'action','run':执行打开},
            })
        子上下文.副作用(登记装饰,'ui-message-feedback: /feedback decoration')
    上下文.依赖启动(['commandUi'],挂命令)

inject=依赖
apply=应用
