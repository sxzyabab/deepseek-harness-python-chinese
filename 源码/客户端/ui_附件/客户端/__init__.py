'浏览器附件插件：撰写栏条目，以及可以单独换掉的图片库'
from . import 标注列表
from . import 撰写附件
from . import 消息图席

__all__=['标注列表','撰写附件','消息图席','依赖','应用']

依赖=['slots']

def 应用(上下文,配置=None):
    '登记撰写附件，以及共用图库和各处图片槽'
    上下文.slots.registerFactory({
        'name':'conversation.images.content',
        'scope':'root',
        'locale':'conversation',
    },消息图席.消息图内容)

    def 登记撰写():
        '输入区附件槽出现后登记撰写附件'
        return 上下文.slots.register({
            'name':'conversation.input.attachments',
            'locale':'conversation',
        },撰写附件.撰写附件)

    上下文.slots.inject('conversation.input.attachments',登记撰写)

    def 登记图片(名):
        '这一处图片槽出现后登记消息图席'
        def 放入():
            '优先级 100，让官方图库盖过空位'
            return 上下文.slots.register({
                'name':名,
                'priority':100,
            },消息图席.消息图席)
        return 上下文.slots.inject(名,放入)

    登记图片('conversation.chat.message.images')
    登记图片('conversation.chat.user.images')
    登记图片('conversation.trajectory.images')
    登记图片('tool.call.images')

inject=依赖
apply=应用
