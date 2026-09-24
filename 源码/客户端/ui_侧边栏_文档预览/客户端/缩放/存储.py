from ....存储 import 声明存储
from .类型 import 适应宽度

__all__=['创建缩放存储','默认缩放']

def 创建缩放存储():
    """标签寿命内记住缩放偏好。"""
    def 缩放(草稿,标签标识,偏好):
        草稿['byTab'][标签标识]=偏好
    def 遗忘(草稿,标签标识):
        表=dict(草稿['byTab'])
        if 标签标识 in 表:
            del 表[标签标识]
        草稿['byTab']=表
    return 声明存储({
        'init':lambda:{'byTab':{}},
        'actions':{'zoom':缩放,'forget':遗忘},
    })

默认缩放=适应宽度
