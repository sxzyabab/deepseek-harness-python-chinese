class 文件树错误(Exception):
    '没有该标签的树。消息与上游 Error 相同，调用方按字符串比对'

    def __init__(自身, 消息):
        '记下上游那句英文'
        super().__init__(消息)
