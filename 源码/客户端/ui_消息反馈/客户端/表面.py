'一场会话的反馈表面：消息列表和对话框，以及两边的提交去向'
from .控制器 import 消息反馈控制器,描述失败
from .对话框 import 反馈对话框控制器

__all__=['反馈表面']

class 反馈表面:
    '支撑一场会话的每个反馈入口'
    def __init__(自身,上下文,会话标识):
        '消息目标走评分，会话目标走 sessionFeedback'
        自身._上下文=上下文
        自身.会话标识=会话标识
        自身.反馈=消息反馈控制器(上下文.remote.messageFeedback,会话标识)
        def 路由(目标,条目):
            '按打开时的目标把这一次提交送出去'
            if 目标['kind']=='message':
                return 自身.反馈.评分(目标['messageId'],目标['rating'],条目)
            请求={'sessionId':自身.会话标识}
            请求.update(条目)
            载体=自身._上下文.remote.sessionFeedback.record(请求)
            if not 载体['ok']:
                return {
                    'ok':False,
                    'error':{
                        'code':载体['error']['code'],
                        'message':载体['error']['message'],
                    },
                }
            if 载体['value']['ok']:
                return {'ok':True}
            码=载体['value']['error']['code']
            return {'ok':False,'error':{'code':码,'message':描述失败(码)}}
        自身.对话框=反馈对话框控制器(路由)

    def 拆除(自身):
        '丢掉消息层和对话框'
        自身.反馈.拆除()
        自身.对话框.拆除()
