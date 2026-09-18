from ...ui_槽位 import 解析槽标签#槽标签

__all__=['行配置键','配置账本源']#仅中文公开名

席位名表=('plugins.item','plugins.bundle.config','plugins.row.config')#三份账本席位

def 行配置键(组合包,行标识):
    """行配置登记键：`<包名>#<行 id>`。"""
    return f'{组合包}#{行标识}'#键

def 配置账本源(上下文):
    """把配置账本投影成页面绑定的可观察源。"""
    版本表=[]#席位版本
    修订=-1#文案修订
    账本={'items':[],'bundles':set(),'rows':set()}#缓存

    def 键集合(名):
        """带键席位的已登记键集。"""
        结果=set()#键集
        for 条目 in 上下文.slots.entries(名):#条目
            选项=条目['options'] if 'options' in 条目 else 条目#选项
            if 'key' in 选项:#有键
                结果.add(选项['key'])#加入
        return 结果#集

    def 取快照():
        """账本或语言未变则复用缓存。"""
        nonlocal 版本表,修订,账本#可变缓存
        下一=[上下文.slots.getVersion(名) for 名 in 席位名表]#版本
        当前=上下文.locale.getSnapshot()['revision']#文案修订
        if 当前!=修订 or 下一!=版本表:#有变
            版本表=下一#记版本
            修订=当前#记修订
            条目表=[]#官方条目
            for 条目 in 上下文.slots.entries('plugins.item'):#列表席
                选项=条目['options'] if 'options' in 条目 else 条目#选项
                身份=选项['id'] if 'id' in 选项 else ''#id
                标签=解析槽标签(选项['label'] if 'label' in 选项 else None)#解析
                if 标签 is None:标签=''#缺省
                条目表.append({'id':身份,'label':标签})#行
            账本={'items':条目表,'bundles':键集合('plugins.bundle.config'),'rows':键集合('plugins.row.config')}#新账本
        return 账本#快照

    def 订阅(监听):
        """席位或语言变动时通知。"""
        拆除表=[上下文.slots.subscribe(名,监听) for 名 in 席位名表]#席位
        拆除表.append(上下文.locale.subscribe(监听))#文案
        def 退订():
            """退订全部。"""
            for 拆 in 拆除表:#逐个
                拆()#退
        return 退订#拆除器

    return {'getSnapshot':取快照,'subscribe':订阅}#可观察源（HostObservable 线形）
