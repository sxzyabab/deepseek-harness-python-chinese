class 原子写入错误(Exception):
    '原子写入或写锁失败'
    def __init__(自身,消息):
        super().__init__(消息)
