from ...异常 import pdf工作线程失败
from .运行时 import 打开pdf
from .文本 import pdf文本渲染器
from ..加载指示器 import 加载指示器
from .文案 import 中文
from ..文案 import 套入

__all__=['pdf体','pdf面板','处理pdf面板','失败文案','样式表']
样式表='''
.body{display:flex;flex-direction:column;gap:12px;box-sizing:border-box;width:100%;min-height:100%;min-width:100%;padding:12px;background:var(--dsw-alias-bg-document-preview);white-space:normal}
.page{box-sizing:border-box;width:100%;min-width:0}
.placeholder{width:100%;aspect-ratio:3/4;background:var(--dsw-alias-bg-skeleton)}
.canvas{display:block;width:100%;height:auto;margin-inline:auto}
'''

默认pdf视图={'page':1}


def 失败文案(错误):
    '把结构化失败写成中文。说明用错误自己的消息'
    if isinstance(错误,pdf工作线程失败):
        return 中文['workerFailed']
    if isinstance(错误,Exception) and getattr(错误,'name',None)=='PasswordException':
        return 中文['password']
    消息=错误.args[0] if isinstance(错误,Exception) and len(错误.args)>0 else str(错误)
    return 套入(中文['failed'],{'message':消息})


def pdf体(内容,取标签信息,取存储,动作,保留标签,翻译):
    '产出 PDF 读取器结构；打开态用 loading 图标位，页含文本层挂钩'
    标签=取标签信息()['tab']
    视图=取存储(lambda 状态:状态['byTab'][标签['id']] if 标签['id'] in 状态['byTab'] else 默认pdf视图)
    数据=内容['data'] if 内容.get('kind')=='bytes' else None
    信号=标签['signal'] if 'signal' in 标签 else None
    保留标签(标签['id'],信号)
    if 数据 is None:
        return {'kind':'pdf-status','status':'unsupported','message':中文['unsupported']}
    def 忽略失败(错误):
        '打开失败由下面的异常接住'
        return None
    会话=打开pdf(数据,信号,忽略失败)
    try:
        文档=会话['document']()
        页数=文档.numPages if hasattr(文档,'numPages') else 0
        return {
            'kind':'pdf-body',
            'pages':页数,
            'view':视图,
            'opening':True,
            'loading':中文['loading'],
            'rendering':中文['rendering'],
            'retry':中文['retry'],
            'textRenderer':pdf文本渲染器,
        }
    except Exception as 错:
        会话['dispose']()
        return {
            'kind':'pdf-status',
            'status':'failed',
            'message':失败文案(错),
            'retry':中文['retry'],
        }


def _键齐(属性):
    '内容、页签、存储和文案都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 'useTabInfo' in 属性 and 'useStore' in 属性 and 't' in 属性

def 处理pdf面板(window,属性):
    '按打开结果画出状态或页占位。有 parent 就挂上去'
    if not _键齐(属性) or '组件' not in 属性:
        return None
    文档=window.document
    if 文档.getElementById('pdf面板样式') is None:
        样式=文档.createElement('style')
        样式.id='pdf面板样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    组件=属性['组件']
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
    if 组件.缓存键!=键 or 组件.模型 is None:
        组件.模型=pdf体(内容,取标签,取存储,动作,保留,翻译)
        组件.缓存键=键
    模型=组件.模型
    if 模型['kind']=='pdf-status':
        状态=文档.createElement('div')
        状态.className='status'
        讯=文档.createElement('div')
        讯.textContent=模型['message']
        状态.appendChild(讯)
        if 模型.get('status')=='failed':
            def 重试(事件):
                '丢掉打开结果再读一次'
                组件.缓存键=None
                组件.模型=None
                组件.渲染()
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent=模型['retry']
            钮.addEventListener('click',重试)
            状态.appendChild(钮)
        if 'parent' in 属性:
            属性['parent'].appendChild(状态)
        return 状态
    体=文档.createElement('div')
    体.className='body'
    if 模型.get('opening') is True:
        体.appendChild(加载指示器({'window':window,'label':模型['loading']}).渲染())
    页数=模型['pages'] if isinstance(模型['pages'],int) else 0
    for 序号 in range(页数):
        页=文档.createElement('div')
        页.className='page placeholder'
        页.setAttribute('aria-label',str(序号+1))
        体.appendChild(页)
    if 'parent' in 属性:
        属性['parent'].appendChild(体)
    return 体

class pdf面板:
    'PDF 页占位、加载与失败重试'

    def __init__(自身,属性):
        '记下文档席 props。有 window 且键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.缓存键=None
        自身.模型=None
        自身.根=None
        if _键齐(自身.属性) and 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '拆掉旧正文，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        if 'window' not in 自身.属性:
            自身.根=None
            return None
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理pdf面板(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
            自身.缓存键=None
            自身.模型=None
        return 自身.渲染()
