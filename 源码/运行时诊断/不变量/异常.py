class 不变量错误(Exception):
    '包拥有的运行时不变量被违反时抛出'
    def __init__(自身,包名,消息):
        '记下包名与英文消息'
        super().__init__('不变量被 "'+包名+'" 违反: '+消息)
        自身.包名=包名
        自身.code='INVARIANT'#稳定机器可读不变量失败码
        自身.name='InvariantError'
