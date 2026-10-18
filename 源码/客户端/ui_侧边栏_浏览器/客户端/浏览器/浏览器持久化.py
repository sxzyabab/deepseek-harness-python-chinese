__all__=['当前浏览器目标']


def 当前浏览器目标(状态):
    '读已保存导航里当前选中的地址。没有记录或下标无效则没有'
    if 状态 is None or 状态['index']<0:
        return None
    return 状态['entries'][状态['index']]
