from ..语言设置 import 本地化错误

__all__=['解析语言引导启动']

def 解析语言引导启动(值):
    """校验预加载 IPC 回传的初始化数据，无持久化副作用。"""
    if not isinstance(值,dict):
        raise 本地化错误('locale: invalid native initialization data')
    if 'languages' not in 值 or not isinstance(值['languages'],list):
        raise 本地化错误('locale: invalid native initialization data')
    for 语言 in 值['languages']:
        if not isinstance(语言,str):
            raise 本地化错误('locale: invalid native initialization data')
    if 'preference' not in 值:
        raise 本地化错误('locale: invalid native initialization data')
    偏好=值['preference']
    if 偏好 is not None and not isinstance(偏好,str):
        raise 本地化错误('locale: invalid native initialization data')
    return {'languages':list(值['languages']),'preference':偏好}
