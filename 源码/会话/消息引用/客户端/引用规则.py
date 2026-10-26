'引用块收成引用节点。相邻段落分隔改成行内空格'
from .引用文本 import 引用文本,消息引用区间

__all__=['引用规则']


def 匹配(文本,起点):
    '从起点往后找下一处引用，或两段之间的空行'
    for 范围 in 消息引用区间(文本):
        for 开始 in (范围['start']-2,范围['start'],范围['end']):
            if 开始<起点:
                continue
            if 开始==范围['start']:
                return {
                    'id':'quote',
                    'start':开始,
                    'end':范围['end'],
                    'data':{'text':引用文本(文本[开始:范围['end']])},
                }
            if 文本[开始:开始+2]=='\n\n':
                return {
                    'id':'text',
                    'start':开始,
                    'end':开始+2,
                    'data':{'text':'\n\n','display':' '},
                }
    return None


引用规则={
    'id':'quote',
    'order':-10,
    'match':匹配,
}
