from ...ui_槽位 import 解析槽标签
from . import 文案
from . import 分区视图

__all__=['文案','分区视图','命名空间','依赖','应用']

命名空间='settings.plugins'
依赖=['slots','locale']

def 应用(上下文,配置=None):
    '挂载内置插件分区和页签壳。各功能页自己登记页签'
    def 登记词典():
        '登记中英文案表。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})
    上下文.副作用(登记词典,'ui-settings-plugins: section dictionaries')
    页签版本=-1
    语言修订=-1
    页签行=[]
    def 分区注入():
        '页签账本的快照。版本或语言没变就返回同一份'
        def 取快照():
            '账本或语言变了才重投影'
            nonlocal 页签版本,语言修订,页签行
            版本=上下文.slots.getVersion('settings.plugins.tab')
            快照=上下文.locale.getSnapshot()
            修订=快照['revision'] if 'revision' in 快照 else None
            if 版本!=页签版本 or 修订!=语言修订:
                页签版本=版本
                语言修订=修订
                下一批=[]
                for 条目 in 上下文.slots.entries('settings.plugins.tab'):
                    选项=条目['options']
                    原文=解析槽标签(选项['label'] if 'label' in 选项 else None)
                    标识=选项['id'] if 'id' in 选项 else None
                    顺序=选项['order'] if 'order' in 选项 else None
                    下一批.append({
                        'id':'' if 标识 is None else 标识,
                        'order':0 if 顺序 is None else 顺序,
                        'label':'' if 原文 is None else 原文,
                    })
                def 页签序(行):
                    '按 order 升序'
                    return 行['order']
                下一批.sort(key=页签序)
                页签行=下一批
            return 页签行
        def 订阅(监听):
            '账本和语言都通知这份快照'
            拆账本=上下文.slots.subscribe('settings.plugins.tab',监听)
            拆语言=上下文.locale.subscribe(监听)
            def 拆除():
                '取消两路订阅'
                拆账本()
                拆语言()
            return 拆除
        return {'hooks':{'tabs':{'getSnapshot':取快照,'subscribe':订阅}}}
    def 导航标签():
        '设置导航上的内置插件'
        return 文案.中文['nav']
    def 登记分区():
        '登记 settings.section 里的内置插件'
        return 上下文.slots.register({
            'name':'settings.section',
            'id':'plugins',
            'order':15,
            'label':导航标签,
            'locale':命名空间,
            'inject':分区注入,
            'children':{'settings.plugins.tab':{'kind':'list','scope':'root'}},
        },分区视图.分区视图)
    上下文.slots.inject('settings.section',登记分区)

inject=依赖
apply=应用
