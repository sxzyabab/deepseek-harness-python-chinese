from .文案 import 中文,英文,侧栏文档预览文案键#词典
from .定义 import 文本预览标识,文本定义#类型定义
from .存储 import 创建文本存储#视图存储
from .面 import 文本面#业务面
from .远程过程调用 import 创建分页读,宿主文件,文档文件字节#远程
from .失败行 import 失败行#失败行
from .文档.注册表 import 文档预览注册表,匹配文档预览#注册表
from .文档.约定 import 文档标签信息工厂#约定
from .文本 import 应用 as 登记纯文本,纯文本体标识#纯文本
from .标记文本 import 应用 as 登记标记文本#Markdown
from .html import 应用 as 登记超文本#HTML
from .图像 import 应用 as 登记图像#图片
from .pdf import 应用 as 登记pdf#PDF
from .代码 import 应用 as 登记代码#代码
from .office import 应用 as 登记Office#Office
from .文本预览 import 文本预览#正文视图模型
from .文本标题 import 文本标题#标题视图模型
from .excel import 应用 as 登记excel#表格
from ..配置 import 默认配置#配置

__all__=[#仅中文公开名
    '依赖',
    '应用',
    '命名空间',
    '中文',
    '英文',
    '侧栏文档预览文案键',
    '文本预览标识',
    '文本定义',
    '创建文本存储',
    '文本面',
    '创建分页读',
    '宿主文件',
    '失败行',
    '文档预览注册表',
    '匹配文档预览',
    '文档标签信息工厂',
    '纯文本体标识',
    '文本预览',
    '文本标题',
]

命名空间='sidebarDocumentPreview'#本包文案命名空间（线路字面量）
依赖=['slots','locale','sidebarRightTabs','remote','remote.workspaceFiles','configForms','resources']#槽、文案、右侧标签、Remote、配置表单、资源


def 应用(上下文):
    """登记类型、词典、正文与芯片标题，并挂各格式渲染器。"""
    配置=默认配置#配置
    预览表=文档预览注册表()#注册表

    def 提供注册表():
        """把注册表挂进上下文。"""
        上下文.documentPreviews=预览表#挂上

        def 拆除():
            """卸下注册表。"""
            if getattr(上下文,'documentPreviews',None) is 预览表:#仍是本份
                delattr(上下文,'documentPreviews')#卸

        return 拆除#拆除器

    上下文.副作用(提供注册表,'ui-sidebar-documentpreview: documentPreviews')#寿命

    def 登记类型():
        """把 text 类型挂进右侧侧栏注册表。"""
        return 上下文.sidebarRightTabs.register(文本定义())#登记

    上下文.副作用(登记类型,'ui-sidebar-documentpreview: text type')#类型寿命

    def 登记词典():
        """挂载中英文案。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记

    上下文.副作用(登记词典,'ui-sidebar-documentpreview: dictionaries')#词典寿命

    存储=创建文本存储()#每会话独占

    def 完整读(文件,信号):
        """完整字节读并解码。"""
        结果=上下文.remote.workspaceFiles.readBytes(文件['sessionId'],文件['path'],{},信号)#读
        if 结果['ok']:#成功
            return {'ok':True,'value':文档文件字节(结果['value'])}#解码
        return 结果#失败原样

    面=文本面(
        创建分页读(上下文.remote),#分页
        完整读,#完整
        上下文.resources,#资源
    )
    源={'getSnapshot':预览表.取快照,'subscribe':预览表.订阅}#快照源（线路字段名）

    def 挂正文():
        """正文进带键席位。"""

        def 登记正文():
            """登记 text 正文。"""
            def 注入面(会话标识,动作):
                """合成 face 与注册表钩。"""
                基=面(会话标识,动作)#业务面
                基['hooks']={'documentPreviews':源}#钩
                return 基#注入

            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab',#席名
                'key':文本预览标识,#实现键
                'locale':命名空间,#文案
                'store':存储,#独占存储
                'children':{#子槽
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
                'inject':注入面,#业务面工厂
            },文本预览)#正文组件

        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)#等洞就绪

    上下文.副作用(挂正文,'ui-sidebar-documentpreview: text body')#正文寿命

    def 挂标题():
        """芯片标题进带键席位。"""

        def 登记标题():
            """登记 text 标题。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab.title',#席名
                'key':文本预览标识,#实现键
            },文本标题)#标题组件

        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)#等洞就绪

    上下文.副作用(挂标题,'ui-sidebar-documentpreview: text title')#标题寿命
    登记纯文本(上下文)#纯文本
    登记标记文本(上下文)#Markdown
    登记超文本(上下文)#HTML
    登记图像(上下文)#图片
    登记pdf(上下文)#PDF
    登记代码(上下文)#代码
    登记Office(上下文,配置.get('office'))#Office
    登记excel(上下文,配置.get('excel'))#表格


inject=依赖#框架槽
apply=应用#框架槽
