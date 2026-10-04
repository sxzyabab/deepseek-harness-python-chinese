'会话标题失败'
__all__=['会话标题错误','会话标题无效错误']#仅中文公开名

class 会话标题错误(Exception):
    '会话标题包的异常基类'

class 会话标题无效错误(会话标题错误):
    '用户标题归一化后为空'
    name='SessionTitleInvalidError'#错误名
