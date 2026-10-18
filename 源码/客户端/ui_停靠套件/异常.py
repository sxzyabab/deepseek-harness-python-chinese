import json

class 停靠错误(Exception):
    '布局引擎拒绝这次操作。消息保持上游英文'
    def __init__(自身,消息):
        '记下上游那句英文'
        super().__init__(消息)

def 未处理(值,何事):
    '闭联合走到了没有的判别'
    raise 停靠错误(f'{何事}: unhandled {json.dumps(值,ensure_ascii=False,separators=(",",":"))}')

def 要求节点空闲(状态,标识):
    '创建操作要求这个节点标识还没有被占用'
    if 标识 in 状态['nodes']:
        raise 停靠错误(f'layout: node {标识} already exists')

def 要求标签空闲(状态,标识):
    '打开操作要求这个标签标识还没有被占用'
    if 标识 in 状态['tabs']:
        raise 停靠错误(f'layout: tab {标识} already exists')
