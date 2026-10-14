'把草稿附件和历史消息图片登记进各自的对话槽'
from .撰写附件 import 撰写附件
from .消息图席 import 消息图席

__all__=['依赖','应用']

依赖=['slots']

def 应用(上下文):
    '只挂输入区附件和消息图片；轨迹图和工具图不在这里再登记'
    def 登记撰写():
        '草稿附件栏'
        return 上下文.slots.register({
            'name':'conversation.input.attachments',
            'locale':'conversation',
        },撰写附件)
    def 挂撰写():
        '等输入区附件槽出现'
        return 上下文.slots.inject('conversation.input.attachments',登记撰写)
    上下文.副作用(挂撰写,'ui-attachment: composer')
    def 登记消息图():
        '历史消息里的图片'
        return 上下文.slots.register({
            'name':'conversation.message.images',
            'locale':'conversation',
        },消息图席)
    def 挂消息图():
        '等消息图片槽出现'
        return 上下文.slots.inject('conversation.message.images',登记消息图)
    上下文.副作用(挂消息图,'ui-attachment: conversation.message.images')

inject=依赖
apply=应用
