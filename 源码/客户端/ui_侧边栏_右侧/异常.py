class 右侧侧栏错误(Exception):
    '右侧栏接线失败。消息保持上游英文原文'


def 未登记种类(种类):
    '没有这个种类的标签类型。认领和放置页面都会抛'
    raise 右侧侧栏错误('sidebarRight: no tab type is registered as "'+str(种类)+'"')


def 无人认领(地址):
    '没有类型认领这个地址。方案不对和排名落空都会抛'
    raise 右侧侧栏错误('sidebarRight: no registered tab type claims "'+str(地址)+'"')
