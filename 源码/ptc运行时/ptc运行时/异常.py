__all__=('ptc运行时错误',)#仅中文公开名

class ptc运行时错误(Exception):
    'PTC 运行时约定误用'
    def __init__(自身,消息):
        '用原样英文消息构造'
        super().__init__(消息)
