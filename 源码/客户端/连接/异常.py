'连接包的异常类。各处就地抛出，文案保持上游原文'


class 连接错误(Exception):
    '宿主或浏览器半边的失败，对应上游 Error'


class 范围错误(Exception):
    '恢复时序不是有限数，对应上游 RangeError'
