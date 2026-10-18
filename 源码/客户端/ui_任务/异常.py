import json

class 任务状态错误(Exception):
    '作业状态不在闭合集合里'

def 断言穷尽(值):
    '闭合状态走到表外'
    raise 任务状态错误('unhandled job status: '+json.dumps(值,ensure_ascii=False))
