from .文案 import 中文,英文

__all__=['应用']

实现键='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/excel'

def 应用(上下文,上限):
    """登记浏览器表格预览及其寿命所属槽。"""
    def 登记词典():
        return 上下文.locale.register('sidebarExcel',{'zh':中文,'en':英文})
    上下文.副作用(登记词典)
    翻译=上下文.locale.bind('sidebarExcel')
    def 登记类型():
        return 上下文.documentPreviews.register({
            'id':实现键,
            'extensions':['xlsx','xls','csv','tsv'],
            'binaryExtensions':['xlsx','xls'],
            'priority':'builtin',
            'title':lambda:翻译('title'),
            'loading':'bytes-complete',
            'wrap':False,
        })
    上下文.副作用(登记类型)
    def 挂正文():
        def 登记正文():
            return 上下文.slots.register({
                'name':'sidebar.right.tab.document',
                'key':实现键,
                'locale':'sidebarExcel',
                'inject':lambda:({'limits':上限}),
            },'LazyExcelBody')
        return 上下文.slots.inject('sidebar.right.tab.document',登记正文)
    上下文.副作用(挂正文)
