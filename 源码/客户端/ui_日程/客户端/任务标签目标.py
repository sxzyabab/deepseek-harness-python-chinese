'从导航参数或存储绑定解析这一页要显示的任务'
from .定义 import 任务参数

__all__=['解析任务标签目标']

def 取(对象,键):
    '字典或对象'
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else None
    return getattr(对象,键,None)

def 解析任务标签目标(会话标识,标签,绑定):
    '有导航参数用导航，否则读上次绑定'
    导航面=取(标签,'navigation')
    参数=取(导航面,'params')
    导航=任务参数(参数)
    已导航=参数 is not None
    页={'id':取(标签,'id'),'kind':取(标签,'kind'),'contentId':取(标签,'contentId')}
    恢复=None if 已导航 or 绑定 is None else 绑定.读取(会话标识,页)
    if 已导航 is False and 绑定 is not None:
        绑定.丢掉不符(会话标识,页)
    return {'navigated':已导航,'navigation':导航,'recovered':恢复,'params':导航 if 导航 is not None else 恢复}
