'图片词典、元数据和正文'
from ..文档.标签寿命 import 保留文档标签
from ..缩放.存储 import 创建缩放存储
from .文案 import 中文,英文
from .图像体 import 图像体

__all__=['文案','图像体','图像体标识','图像扩展','二进制图像扩展','应用']

图像体标识='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/image'
图像扩展=('png','jpg','jpeg','gif','webp','bmp','ico','svg')
二进制图像扩展=('png','jpg','jpeg','gif','webp','bmp','ico')

def 应用(上下文,配置=None):
    '登记图片词典、元数据和正文。SVG 不进二进制名单，源文本仍值得读'
    def 登记词典():
        '登记中英文案表。页面显示不走英文表'
        return 上下文.locale.register('sidebarImage',{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'document-image: dictionaries')
    def 标题():
        '实现名。是图片'
        return 中文['title']
    def 登记元数据():
        '登记图片后缀'
        return 上下文.documentPreviews.登记({
            'id':图像体标识,
            'extensions':图像扩展,
            'binaryExtensions':二进制图像扩展,
            'priority':'builtin',
            'title':标题,
            'loading':'bytes-complete',
            'wrap':False,
        })
    上下文.副作用(登记元数据,'document-image: metadata')
    存储=创建缩放存储()
    拿住=保留文档标签(上下文)
    def 登记正文():
        '挂上图片正文，并按标签寿命忘掉缩放'
        def 登记():
            '登记图像体'
            def 注入(会话标识,动作):
                '标签结束时忘掉缩放'
                def 保留(标签标识,信号):
                    '拿住这一标签'
                    拿住(标签标识,信号,动作['forget'])
                return {'retainTab':保留}
            return 上下文.slots.register({
                'name':'sidebar.right.tab.document',
                'key':图像体标识,
                'locale':'sidebarImage',
                'store':存储,
                'inject':注入,
            },图像体)
        return 上下文.slots.inject('sidebar.right.tab.document',登记)
    上下文.副作用(登记正文,'document-image: body')
