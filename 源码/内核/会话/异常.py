class 会话错误(Exception):
    '内核会话包的异常基类'

class 会话分叉错误(Exception):#分叉错误
    '会话分叉拒绝的带类型错误（码：SESSION_NOT_FOUND / SESSION_NOT_LIVE / SESSION_ALREADY_EXISTS / INVALID_BOUNDARY / OPEN_TURN）'
    def __init__(自身,消息,码):#带拒绝码
        '带拒绝码'
        super().__init__(消息)#错误文案
        自身.message=消息#可读消息
        自身.code=码#拒绝码
        自身.name='SessionForkError'#固定名（错误类协议名）

class 表面错误(Exception):
    '内核会话表面包的异常基类'

class 块行错误(Exception):
    '内核会话块行包的异常基类'
