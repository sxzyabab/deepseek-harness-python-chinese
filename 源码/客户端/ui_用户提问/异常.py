'提问卡片交回宿主的线路拒绝。页面上的字不从这里取'

拒绝文案={#线路保留的英文原因。页面不显示
    'ASK_ABORTED':'ask_user_question was aborted before the user answered',#中止
    'ASK_CANCELLED':'the user cancelled ask_user_question',#用户取消
    'ASK_TIMED_OUT':'ask_user_question timed out before the user answered',#超时
}


class 提问拒绝(Exception):
    '线路保留的提问拒绝。name 和 code 要能被宿主认出来'
    def __init__(自身,码):
        '按码记下英文原因，并标成 UserQuestionError'
        super().__init__(拒绝文案[码])#英文原因
        自身.name='UserQuestionError'#固定名
        自身.code=码#稳定码
