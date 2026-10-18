'浏览器半：把 text 登记成右侧侧栏标签类型'
from ..配置 import 配置
from ....工具.工作区路径 import 解析文件地址
from .文案 import 中文,英文
from .定义 import 文本预览种类,文本预览标识,基名
from .存储 import 创建文本存储
from .面 import 文本面
from .远程过程调用 import 创建分页读,文档文件字节
from .文档.约定 import 文档标签信息工厂
from .文档.注册表 import 文档预览注册表
from .文本预览 import 文本预览
from .文本标题 import 文本标题
from .文本 import 应用 as 登记纯文本
from .标记文本 import 应用 as 登记标记文本
from .html import 应用 as 登记超文本
from .图像 import 应用 as 登记图像
from .pdf import 应用 as 登记pdf
from .代码 import 应用 as 登记代码
from .office import 应用 as 登记Office
from .excel import 应用 as 登记表格
from . import (
    文案,
    定义,
    失败行,
    存储,
    远程过程调用,
    面,
    加载指示器,
    文本标题,
    文本预览,
    文档,
    文本,
    图像,
    代码,
    缩放,
    标记文本,
    html,
    pdf,
    office,
    excel,
)

__all__=[
    '命名空间','依赖','应用',
    '文案','定义','失败行','存储','远程过程调用','面',
    '加载指示器','文本标题','文本预览','文档','文本',
    '图像','代码','缩放','标记文本','html','pdf','office','excel',
]

命名空间='sidebarDocumentPreview'
依赖=['slots','locale','sidebarRightTabs','remote','remote.workspaceFiles','configForms','resources']

def 应用(上下文,配置=None):
    '登记类型、词典、正文与芯片标题，并挂各格式渲染器'
    try:
        原始=__DSH_DOCUMENT_PREVIEW_CONFIG__
    except NameError:
        原始=None
    if 原始 is None:
        原始={}
    上限=配置(原始)
    预览表=文档预览注册表()
    def 提供注册表():
        '交出 documentPreviews。返回值是拆除器'
        return 上下文.reflect.provide('documentPreviews',预览表)
    上下文.副作用(提供注册表)
    def 标题名(地址):
        '芯片标题用解码后的文件名'
        return 基名(地址)
    def 能否打开(地址):
        '只认带会话的文件地址'
        解析=解析文件地址(地址)
        return isinstance(解析,dict) and 解析.get('scope')=='session'
    def 登记类型():
        '登记 text 类型。优先级是回落'
        return 上下文.sidebarRightTabs.register({
            'id':文本预览标识,
            'kind':文本预览种类,
            'patterns':['dsh-resource://file/[\\s\\S]+'],
            'priority':'fallback',
            'canOpen':能否打开,
            'title':标题名,
        })
    上下文.副作用(登记类型,'ui-sidebar-documentpreview: text type')
    def 登记词典():
        '登记中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'ui-sidebar-documentpreview: dictionaries')
    存储句柄=创建文本存储()
    def 完整读(文件,信号):
        '完整字节读。成功时把 data 解成字节'
        待=上下文.remote.workspaceFiles.readBytes(文件['sessionId'],文件['path'],{},信号)
        结果=待.等待() if hasattr(待,'等待') else 待
        if 结果['ok']:
            return {'ok':True,'value':文档文件字节(结果['value'])}
        return 结果
    面=文本面(创建分页读(上下文.remote),完整读,上下文.resources)
    源={'getSnapshot':预览表.getSnapshot,'subscribe':预览表.subscribe}
    def 挂正文():
        '正文进带键席位'
        def 登记正文():
            '登记文本预览'
            def 注入面(会话标识,动作):
                '业务面加上预览登记表钩子'
                基=面(会话标识,动作)
                基['hooks']={'documentPreviews':源}
                return 基
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab',
                'key':文本预览标识,
                'locale':命名空间,
                'store':存储句柄,
                'children':{
                    'sidebar.right.tab.document':{
                        'kind':'keyed',
                        'scope':'session',
                        'inject':{'hooks':{'tabInfo':文档标签信息工厂}},
                    },
                    'sidebar.right.tab.document.actions':{'kind':'list','scope':'session'},
                    'sidebar.right.tab.document.unpreviewable':{'kind':'list','scope':'session'},
                    'sidebar.right.tab.document.action':{
                        'kind':'keyed',
                        'scope':'session',
                        'inject':{'hooks':{'tabInfo':文档标签信息工厂}},
                    },
                },
                'inject':注入面,
            },文本预览)
        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)
    上下文.副作用(挂正文,'ui-sidebar-documentpreview: text body')
    def 挂标题():
        '芯片标题进带键席位'
        def 登记标题():
            '登记文本标题'
            return 上下文.slots.register({
                'name':'sidebar.right.pane.tab.title',
                'key':文本预览标识,
            },文本标题)
        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)
    上下文.副作用(挂标题,'ui-sidebar-documentpreview: text title')
    登记纯文本(上下文)
    登记标记文本(上下文)
    登记超文本(上下文)
    登记图像(上下文)
    登记pdf(上下文)
    登记代码(上下文)
    登记Office(上下文,上限['office'])
    登记表格(上下文,上限['excel'])

inject=依赖
apply=应用
