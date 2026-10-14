__all__=['工具视图键','创建仓','运行卡片注册表']#仅中文公开名

def 工具视图键(插件标识,包标识):
    'pluginId.packageId'
    return f'{插件标识}.{包标识}'

def 创建仓():
    'getSnapshot / subscribe / observe；更大 seq 才能替换'
    指针表={}
    监听集合=set()
    缓存=None

    def 快照():
        '惰性拷贝'
        nonlocal 缓存
        if 缓存 is None:
            缓存=dict(指针表)
        return 缓存

    def 订阅(监听器):
        '登记并返回退订'
        监听集合.add(监听器)
        def 退订():
            '移除'
            监听集合.discard(监听器)
        return 退订

    def 观察(指针):
        '序号不更大则忽略'
        nonlocal 缓存
        键=指针.get('key') if isinstance(指针,dict) else None
        现有=指针表.get(键)
        if 现有 is not None and 现有.get('seq',-1)>=指针.get('seq',-1):#序号不更大则忽略
            return
        指针表[键]=指针
        缓存=None
        for 监听器 in list(监听集合):
            监听器()

    return {'getSnapshot':快照,'subscribe':订阅,'observe':观察}

class 运行卡片注册表:
    '页生命周期：同会话卡片共用一仓'

    def __init__(自身):
        '空表'
        自身.会话表={}

    def 取会话(自身,会话标识):
        '返回该会话持久仓'
        仓=自身.会话表.get(会话标识)
        if 仓 is None:
            仓=创建仓()
            自身.会话表[会话标识]=仓
        return 仓
