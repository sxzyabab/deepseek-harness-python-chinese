__all__=['工具视图键','创建仓','运行卡片注册表']#仅中文公开名

def 工具视图键(插件标识,包标识):#拼业务视图键
    """pluginId.packageId。"""
    return f'{插件标识}.{包标识}'#拼接

def 创建仓():#新建会话内仓
    """getSnapshot / subscribe / observe；更大 seq 才能替换。"""
    指针表={}#键 → 指针
    监听集合=set()#订阅者
    缓存=None#快照

    def 快照():#读快照
        """惰性拷贝。"""
        nonlocal 缓存#闭包
        if 缓存 is None:#无
            缓存=dict(指针表)#拷
        return 缓存#快照

    def 订阅(监听器):#订阅
        """登记并返回退订。"""
        监听集合.add(监听器)#加
        def 退订():#退订
            """移除。"""
            监听集合.discard(监听器)#丢
        return 退订#退订

    def 观察(指针):#发布
        """序号不更大则忽略。"""
        nonlocal 缓存#闭包
        键=指针.get('key') if isinstance(指针,dict) else None#键
        现有=指针表.get(键)#现有
        if 现有 is not None and 现有.get('seq',-1)>=指针.get('seq',-1):#不更大
            return#忽略
        指针表[键]=指针#写
        缓存=None#作废
        for 监听器 in list(监听集合):#通知
            监听器()#触发

    return {'getSnapshot':快照,'subscribe':订阅,'observe':观察}#仓

class 运行卡片注册表:#按会话分仓
    """页生命周期：同会话卡片共用一仓。"""

    def __init__(自身):#构造
        """空表。"""
        自身.会话表={}#会话 → 仓

    def 取会话(自身,会话标识):#取或建
        """返回该会话持久仓。"""
        仓=自身.会话表.get(会话标识)#已有
        if 仓 is None:#无
            仓=创建仓()#建
            自身.会话表[会话标识]=仓#记
        return 仓#仓
