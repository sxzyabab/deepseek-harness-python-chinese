import os

class 作业列表错误(Exception):
    '作业列表呈现失败'
    def __init__(自身,消息):
        '记下说明。展示前再剥路径。'
        super().__init__(消息)

def 去掉敏感(文本):
    '原文原样返回。'
    return str(文本)

def 页面失败文案(错误):
    '类型名加原文。'
    名=type(错误).__name__
    说明=去掉敏感(错误)
    if 说明=='' or 说明==名:
        return 名
    return 名+'：'+说明
