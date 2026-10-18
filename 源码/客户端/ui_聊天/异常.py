__all__=['聊天错误','抛未知会话']


class 聊天错误(Exception):
    'ui-chat 包内抛出的失败。消息与上游 Error 原文一致'


def 抛未知会话(会话标识):
    '流或视图登记时，这份会话没有绑定'
    raise 聊天错误('ui-chat: unknown session "'+str(会话标识)+'"')
