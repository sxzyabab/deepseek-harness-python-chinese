class Webhook错误(Exception):
    '本包异常基类'

class Webhook已中止(Webhook错误):
    '规则拆除导致的中止'

class 会话错误(Exception):
    'webhook 会话创建路径上的失败'

class 会话查询错误中止(会话错误):
    'webhook 创建路径上的取消'
