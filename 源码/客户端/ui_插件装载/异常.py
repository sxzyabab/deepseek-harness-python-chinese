class 远程应答错误(Exception):
    '拒绝应答或 Host 未能应用的变更'
    def __init__(自身,原因,码=None):
        '记下原因与可选拒码'
        super().__init__(原因)#消息
        自身.原因=原因#原因
        自身.码=码
