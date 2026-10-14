from nicegui import ui as 界面
from .运行时 import 打开pdf
from ...异常 import pdf工作线程失败,去掉敏感
from .文本 import pdf文本渲染器
from ..加载指示器 import 加载状态

__all__=['pdf体','pdf面板','失败文案','样式表']
样式表='''
.body{display:flex;flex-direction:column;gap:12px;box-sizing:border-box;width:100%;min-height:100%;min-width:100%;padding:12px;background:var(--dsw-alias-bg-document-preview);white-space:normal}
.page{box-sizing:border-box;width:100%;min-width:0}
.placeholder{width:100%;aspect-ratio:3/4;background:var(--dsw-alias-bg-skeleton)}
.canvas{display:block;width:100%;height:auto;margin-inline:auto}
'''
界面.add_css(样式表,shared=True)

默认pdf视图={'page':1}#与远程 DEFAULT_PDF_VIEW 对齐


def 失败文案(错误,翻译):
    '把结构化失败翻成可见行'
    if isinstance(错误,pdf工作线程失败):
        return 翻译('workerFailed')#工作线程
    if isinstance(错误,Exception) and getattr(错误,'name',None)=='PasswordException':
        return 翻译('password')#密码
    消息=错误.args[0] if isinstance(错误,Exception) and len(错误.args)>0 else str(错误)
    return 翻译('failed',{'message':去掉敏感(消息)})


def pdf体(内容,取标签信息,取存储,动作,保留标签,翻译):
    '产出 PDF 读取器结构；打开态用 loading 图标位，页含文本层挂钩'
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


def _键齐(属性):
    '内容、页签、存储和文案都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 'useTabInfo' in 属性 and 'useStore' in 属性 and 't' in 属性

class pdf面板:
    'PDF 页占位、加载与失败重试'

    def __init__(自身,属性):
        '记下文档席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.缓存键=None
        自身.模型=None
        if _键齐(自身.属性):
            自身.渲染()

    def 渲染(自身):
        '按打开结果画出状态或页占位'
        属性=自身.属性
        if not _键齐(属性):
            return
        内容=属性['content']
        取标签=属性['useTabInfo']
        取存储=属性['useStore']
        动作=属性['actions'] if 'actions' in 属性 else None
        保留=属性['retainTab'] if 'retainTab' in 属性 else None
        翻译=属性['t']
        if 保留 is None:
            def 保留(*参数):
                '无保留钩子时不做事'
                return None
        if 动作 is None:
            动作={}
        数据=内容['data'] if isinstance(内容,dict) and 内容.get('kind')=='bytes' else None
        键=id(数据) if 数据 is not None else None
        if 自身.缓存键!=键 or 自身.模型 is None:
            自身.模型=pdf体(内容,取标签,取存储,动作,保留,翻译)
            自身.缓存键=键
        模型=自身.模型
        if 模型['kind']=='pdf-status':
            with 界面.column().classes('status'):
                界面.label(模型['message'])
                if 模型.get('status')=='failed':
                    def 重试():
                        '丢掉打开结果再读一次'
                        自身.缓存键=None
                        自身.模型=None
                        自身.渲染()
                    界面.button(模型['retry'], on_click=重试)
            return
        with 界面.column().classes('body'):
            if 模型.get('opening') is True:
                加载状态(模型['loading']).渲染()
            页数=模型['pages'] if isinstance(模型['pages'],int) else 0
            for 序号 in range(页数):
                界面.element('div').classes('page placeholder').props('aria-label="'+str(序号+1)+'"')

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
            自身.缓存键=None
            自身.模型=None
        return 自身.渲染()
