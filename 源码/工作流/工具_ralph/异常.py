class 错误(Exception):#英文文案
    '运行时错误，详情保持英文原文'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        Exception.__init__(自身,消息)#英文消息
