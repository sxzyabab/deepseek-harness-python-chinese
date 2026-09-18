from .运行时 import 打开pdf#打开
from .错误 import pdf工作线程失败#失败
from .文本 import pdf文本渲染器#文本层

__all__=['pdf体','失败文案']#仅中文公开名

默认pdf视图={'page':1}#与远程 DEFAULT_PDF_VIEW 对齐


def 失败文案(错误,翻译):
    """把结构化失败翻成可见行。"""
    if isinstance(错误,pdf工作线程失败) or (isinstance(错误,Exception) and getattr(错误,'name',None)=='PdfWorkerFailure'):
        return 翻译('workerFailed')#工作线程
    if isinstance(错误,Exception) and getattr(错误,'name',None)=='PasswordException':
        return 翻译('password')#密码
    消息=错误.args[0] if isinstance(错误,Exception) and len(错误.args)>0 else str(错误)#消息
    return 翻译('failed',{'message':消息})#通用


def pdf体(内容,取标签信息,取存储,动作,保留标签,翻译):
    """产出 PDF 读取器结构；打开态用 loading 图标位，页含文本层挂钩。"""
    标签=取标签信息()['tab']#标签
    视图=取存储(lambda 状态:状态['byTab'][标签['id']] if 标签['id'] in 状态['byTab'] else 默认pdf视图)#视图
    数据=内容['data'] if 内容.get('kind')=='bytes' else None#字节
    信号=标签['signal'] if 'signal' in 标签 else None#寿命
    保留标签(标签['id'],信号)#保留偏好
    if 数据 is None:#非字节
        return {'kind':'pdf-status','status':'unsupported','message':翻译('unsupported')}#状态
    会话=打开pdf(数据,信号,lambda 错:None)#打开
    try:
        文档=会话['document']()#加载
        页数=文档.numPages if hasattr(文档,'numPages') else 0#页数
        return {#结构
            'kind':'pdf-body',
            'pages':页数,
            'view':视图,
            'opening':True,#data-document-loading
            'loading':翻译('loading'),
            'rendering':翻译('rendering'),
            'retry':翻译('retry'),
            'textRenderer':pdf文本渲染器,#页文本层
        }#结束
    except Exception as 错:#失败
        会话['dispose']()#清
        return {#状态
            'kind':'pdf-status',
            'status':'failed',
            'message':失败文案(错,翻译),
            'retry':翻译('retry'),
        }#结束
