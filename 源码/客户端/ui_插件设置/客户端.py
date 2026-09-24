from .文案 import 命名空间,中文,英文#词典
from .分区视图 import 插件设置分区#分区壳

__all__=['依赖','应用','插件设置分区','命名空间','中文','英文']

依赖=['slots','locale']#槽位与文案

def 解析槽标签(标签):
    """字符串或 thunk。"""
    if 标签 is None:
        return ''
    if callable(标签):
        结果=标签()
        return 结果 if 结果 is not None else ''
    return str(标签)

def 应用(上下文):
    """挂载内置插件设置分区与页签壳。配置页由配套包装登记。"""
    翻译=上下文.locale.bind(命名空间)
    def 登记词典():
        """把插件设置词表写进 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-settings-plugins: section dictionaries')
    页签版本=-1
    语言修订=-1
    页签行=[]
    def 分区注入():
        """页签可观察源。"""
        def 取快照():
            """账本或语言变了才重投影。"""
            nonlocal 页签版本,语言修订,页签行
            版本=上下文.slots.getVersion('settings.plugins.tab')
            快照=上下文.locale.getSnapshot()
            修订=快照['revision'] if 'revision' in 快照 else None
            if 版本!=页签版本 or 修订!=语言修订:
                页签版本=版本
                语言修订=修订
                页签行=[]
                for 条目 in 上下文.slots.entries('settings.plugins.tab'):
                    选项=条目['options'] if 'options' in 条目 else 条目
                    页签行.append({
                        'id':选项['id'] if 'id' in 选项 else '',
                        'order':选项['order'] if 'order' in 选项 else 0,
                        'label':解析槽标签(选项['label'] if 'label' in 选项 else None),
                    })
                def 页签序(行):
                    """升序。"""
                    return 行['order']
                页签行.sort(key=页签序)
            return 页签行
        def 订阅(监听):
            """两路订阅。"""
            拆账本=上下文.slots.subscribe('settings.plugins.tab',监听)
            拆语言=上下文.locale.subscribe(监听)
            def 拆除():
                """取消。"""
                拆账本()
                拆语言()
            return 拆除
        return {'hooks':{'tabs':{'getSnapshot':取快照,'subscribe':订阅}}}
    def 导航标签():
        """插件设置导航标签。"""
        return 翻译('nav')
    def 登记分区():
        """登记 settings.section 条目。"""
        return 上下文.slots.register({
            'name':'settings.section',
            'id':'plugins',
            'order':15,
            'label':导航标签,
            'locale':命名空间,
            'inject':分区注入,
            'children':{'settings.plugins.tab':{'kind':'list','scope':'root'}},
        },插件设置分区)
    上下文.slots.inject('settings.section',登记分区)

inject=依赖
apply=应用
