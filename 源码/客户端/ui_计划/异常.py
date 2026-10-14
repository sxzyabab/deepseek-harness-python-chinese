import os

class 计划错误(Exception):
    '退出计划模式失败'
    def __init__(自身,消息):
        '记下英文消息'
        super().__init__(消息)#消息原样英文

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
