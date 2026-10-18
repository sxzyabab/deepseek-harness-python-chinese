'changes-review 右侧边栏标签种：一轮改动文件的逐文件对比'
from ..改动 import 解析改动审阅地址
from .文案 import 中文,填入

__all__=['改动审阅种','改动审阅标识','改动审阅定义']

改动审阅种='changes-review'
改动审阅标识='@deepseek-ai/dsh-client-ui-deliverables'


def 改动审阅定义():
    '标题用中文表里的第几轮。地址认不出来就原样显示'
    def 能打开(地址):
        '只有本包签发的审阅地址能开'
        return 解析改动审阅地址(地址) is not None

    def 标题(地址):
        '标签标题。回合号来自地址'
        坐标=解析改动审阅地址(地址)
        if 坐标 is None:
            return 地址
        return 填入(中文['review.title'],{'turn':str(坐标['turn'])})

    return {
        'id':改动审阅标识,
        'kind':改动审阅种,
        'patterns':['dsh-resource://changes-review/**'],
        'priority':'builtin',
        'canOpen':能打开,
        'title':标题,
    }
