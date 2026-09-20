"""对外会话面约定：行为动词 + 生命周期读侧。

实现见 `客户端/会话.py`；本模块只列期望动词。
"""
__all__=['会话面动词']#仅中文公开名

会话面动词=(#ISession 动词
    'beginSubmission','prompt','readAttachment','updateQueue',
    'cancel','rename','loadOlder','loadThrough','command',
)#动词结束
