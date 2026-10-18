class 审批委托(Exception):
    '未作答的审批交给瀑布下一环时的标记。页面不显示这句话'
    def __init__(自身,标记):
        '记下这一次委托的身份，用来和别的失败分开'
        super().__init__('pending approval delegated')#与上游符号说明一致
        自身.标记=标记#这一次委托的身份
