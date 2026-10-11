'两张虚拟检查表格共用的行身份和原始值'

__all__=['行已折叠','检查器表格层级','检查器记录源']

def 行已折叠(行,选择):
    '用手选或块生命周期默认值判断后代是否隐藏'
    抉择=选择.get(行['key'])
    if 抉择 is not None and 抉择['state']==行.get('disclosure'):
        return 抉择['collapsed']
    return 行.get('disclosure')=='closed'

class 检查器表格层级:
    '表格局部的展开索引，供折叠和虚拟吸顶祖先使用'
    def __init__(自身,行表,选择):
        '按深度优先顺序丢掉已折叠的后代'
        可见=[]
        隐藏深度=None
        自身._按键={}
        自身._分支=set()
        for 行 in 行表:
            if 行.get('parent') is not None:
                自身._分支.add(行['parent'])
            if 行.get('disclosure') is not None:
                自身._分支.add(行['key'])
            if 隐藏深度 is not None and 行['depth']>隐藏深度:
                continue
            隐藏深度=行['depth'] if 行已折叠(行,选择) else None
            自身._按键[行['key']]=len(可见)
            可见.append(行)
        自身.行=可见

    def 是分支(自身,键):
        '该行是否拥有后代或显式展开状态'
        return 键 in 自身._分支

    def 吸顶下标(自身,下标):
        '当前行可见的父级表头，自身是表头时也包括自己'
        下标表=[]
        行=自身.行[下标] if 0<=下标<len(自身.行) else None
        if 行 is not None and 自身.是分支(行['key']):
            下标表.append(下标)
        while 行 is not None and 行.get('parent') is not None:
            父=自身._按键.get(行['parent'])
            if 父 is None:
                break
            下标表.append(父)
            行=自身.行[父]
        下标表.reverse()
        return 下标表

class 检查器记录源:
    '把带键来源转成检查记录；输入不变时不换快照身份'
    def __init__(自身,来源,投影):
        '来源是已有的带键业务源；投影只在输入变化后求值'
        自身._来源=来源
        自身._投影=投影
        自身._先前=None
        自身._见过=False
        自身._快照=None

    def getSnapshot(自身):
        '当前原始值的稳定元数据'
        值=自身._来源.getSnapshot()
        if not 自身._见过 or 值 is not 自身._先前:
            自身._见过=True
            自身._先前=值
            自身._快照=None if 值 is None else 自身._投影(值)
        return 自身._快照

    def subscribe(自身,监听):
        '行失效回调，返回其卸除函数'
        return 自身._来源.subscribe(监听)
