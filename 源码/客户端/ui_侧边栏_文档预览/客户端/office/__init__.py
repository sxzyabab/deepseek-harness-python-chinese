"""经授权 Host 渲染与既有 PDF 正文支撑的 Office 预览登记。"""
from ..文档.标签寿命 import 保留文档标签#标签寿命
from ..远程过程调用 import 文档文件字节#文档字节
from ..失败行 import 失败行#失败行
from ..文档.约定 import 文档标签信息工厂#文档标签信息
from .文案 import 中文,英文#文案
from .缓存 import Office预览缓存#缓存
from .存储 import 创建Office存储#存储
from ..pdf import 应用 as 登记pdf呈现#PDF 呈现登记占位

__all__=['应用','转换错误键']#仅中文公开名

扩展名=['doc','docx','xls','xlsx','ppt','pptx']#扩展名
实现键='@deepseek-ai/dsh-client-ui-sidebar-documentpreview/office'#实现键

def 转换错误键(代码):
    """Host 转换错误码映射文案键。"""
    if 代码 in ('input-too-large','output-too-large'):#过大
        return 'tooLarge'#过大
    if 代码 in ('invalid-document','unsupported-format'):#无效
        return 'invalid'#无效
    if 代码=='timeout':#超时
        return 'timeout'#超时
    if 代码=='unavailable':#不可用
        return 'unavailable'#不可用
    if 代码=='busy':#忙
        return 'busy'#忙
    if 代码=='source-changed':#已变
        return 'changed'#已变
    return 'failed'#通用

def 应用(上下文,配置):
    """以版本化 PDF 复用与缺字体提示登记 Office 预览。配置含缓存上限。"""
    def 登记词典():
        """挂 Office 词典。"""
        return 上下文.locale.register('sidebarOffice',{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典)#寿命
    翻译=上下文.locale.bind('sidebarOffice')#翻译
    def 不可用读(文件,信号):
        """不可用时拒绝。"""
        文件#源
        if hasattr(信号,'throwIfAborted'):#中止
            信号.throwIfAborted()#抛
        raise RuntimeError(翻译('unavailable'))#拒绝
    当前读=[不可用读]#可变读
    def 登记类型():
        """挂预览类型。"""
        return 上下文.documentPreviews.register({#登记
            'id':实现键,#键
            'extensions':扩展名,#扩展
            'binaryExtensions':扩展名,#二进制扩展
            'priority':'builtin',#内建
            'title':lambda:翻译('title'),#标题
            'loading':'renderer',#渲染器加载
            'wrap':False,#不换行
        })
    上下文.副作用(登记类型)#寿命
    存储=创建Office存储()#存储
    保留标签=保留文档标签(上下文)#保留
    文档翻译=上下文.locale.bind('sidebarDocumentPreview')#文档文案
    def 描述失败(失败信息):
        """本地化失败。"""
        if isinstance(失败信息,dict) and 'code' in 失败信息:#远程失败
            return 失败行(文档翻译,失败信息)#失败行
        return 文档翻译('error.unavailable',{'message':失败信息.get('message') if isinstance(失败信息,dict) else str(失败信息)})#通用
    def 注入(_会话标识,动作):
        """正文注入。"""
        def 保留(标签标识,信号):
            """保留至忘记。"""
            保留标签(标签标识,信号,动作['forget'])#保留
        def 读(文件,信号):
            """转当前读。"""
            return 当前读[0](文件,信号)#读
        return {'read':读,'describeFailure':描述失败,'retainTab':保留}#注入
    def 登记正文():
        """挂 Office 正文槽。"""
        return 上下文.slots.inject('sidebar.right.tab.document',lambda:上下文.slots.register({#登记
            'name':'sidebar.right.tab.document',#名
            'key':实现键,#键
            'locale':'sidebarOffice',#文案
            'store':存储,#存储
            'inject':注入,#注入
        },'OfficeBody'))#组件名占位
    上下文.副作用(登记正文)#寿命
    登记pdf呈现(上下文)#PDF 子呈现
    配置#缓存上限供 Host 注入使用
    Office预览缓存#缓存类型可被 Host 注入构造
    文档文件字节#字节转换可用
