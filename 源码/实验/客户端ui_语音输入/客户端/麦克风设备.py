'浏览器本地的麦克风选择，和 Host 识别设置分开保存'

__all__=['创建麦克风设备存储','快照仓']

class 快照仓:
    'getSnapshot / set / subscribe'
    def __init__(自身,初值):
        '记下初值'
        自身._状态=初值
        自身._监听=set()

    def getSnapshot(自身):
        '当前设备'
        return 自身._状态

    def set(自身,次值):
        '写入并通知'
        自身._状态=次值
        for 监听 in list(自身._监听):
            监听()

    def subscribe(自身,监听):
        '返回退订'
        自身._监听.add(监听)
        def 退订():
            '去掉这一个监听'
            自身._监听.discard(监听)
        return 退订

def 合法设备(值):
    'id 与 label 都必须是字符串；空 id 表示跟随系统输入'
    if not isinstance(值,dict):
        return False
    return isinstance(值.get('id'),str) and isinstance(值.get('label'),str)

def 创建麦克风设备存储():
    '缺省跟随系统输入'
    存储=快照仓({'id':'','label':''})
    已存=存储.getSnapshot()
    if not 合法设备(已存):
        存储.set({'id':'','label':''})
    return 存储
