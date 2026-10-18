'从导航参数或存下的绑定解析这一页要看的任务'
from ...模块.客户端.通告 import 取握手窗口

__all__=['用任务标签目标']

def 用任务标签目标(会话标识,页,绑定):
    '有导航就用导航。恢复的页才读绑定，并在画完后丢掉不配的条目'
    参数=页['navigation']['params'] if isinstance(页.get('navigation'),dict) else None
    导航=None
    已导航=参数 is not None
    if isinstance(参数,dict) and 'sessionId' in 参数 and 'id' in 参数:
        导航={'sessionId':参数['sessionId'],'id':参数['id']}
    页面={'id':页['id'],'kind':页['kind'],'contentId':页['contentId']}
    恢复=None if 已导航 else 绑定.读取(会话标识,页面)
    if not 已导航:
        def 丢掉():
            '这一帧读完再删不配的条目'
            绑定.丢掉不配(会话标识,页面)
        取握手窗口().queueMicrotask(丢掉)
    return {'navigated':已导航,'navigation':导航,'recovered':恢复,'params':导航 if 导航 is not None else 恢复}
