'Office 拥有源加载、转换失败与缺字体提示，环绕共享 PDF 视图'
from ....ui_基础界面组件.文件类型图标 import 文件类型图标
from ..加载指示器 import 加载指示器
from ..远程过程调用 import 宿主文件
from .字体提示 import 字体提示,字体提示条

def _键齐(属性):
    '页签、存储、内容、文案、保留和 PDF 子槽都在才画'
    if not isinstance(属性,dict):
        return False
    for 键 in ('useTabInfo','useStore','content','resourceAddress','t','retainTab','load','renderSlot'):
        if 键 not in 属性:
            return False
    return True

__all__=['Office正文','办公正文','处理办公正文','样式表']

样式表='''
.body{display:flex;flex-direction:column;height:100%;min-height:0}
.empty{display:flex;flex-direction:column}
'''

def Office正文(属性):
    '加载一次 Office 修订并保留至标签关闭。属性为合成 props'
    标签信息=属性['useTabInfo']()
    标签=标签信息['tab']
    保留标签=属性['retainTab']
    资源地址=属性['resourceAddress']
    翻译=属性['t']
    内容=属性['content']
    请求=内容 if 内容.get('kind')=='renderer' else None
    if 请求 is None:
        return None
    修订=请求.get('revision')
    持有=属性['useStore'](lambda 状态:状态['byTab'].get(标签['id']))
    视图=持有 if 持有 is not None and 持有.get('revision')==修订 else None
    保留标签(标签['id'],标签.get('signal'))
    if 视图 is not None and 视图.get('failure') is not None:
        return {'kind':'office-failed','code':视图['failure']['code'],'message':视图['failure']['message'],'retry':翻译('retry')}
    if 视图 is None or 'file' not in 视图:
        return {'kind':'office-loading','label':翻译('loading')}
    文件=视图['file']
    return {
        'kind':'office-body',
        'fontNotice':字体提示({'resourceAddress':资源地址,'sourceVersion':文件.get('version'),'fonts':文件.get('missingFonts',[]),'t':翻译}),
        'pdf':{'kind':'bytes','data':文件.get('data')},
    }


def _挂上(容器,结果):
    '子槽返回节点就挂上'
    if isinstance(结果,dict) and 结果.get('type')=='slot-outlet':
        结果=结果.get('content')
    if getattr(结果,'tagName',None) is None and getattr(结果,'nodeType',None) is None:
        return
    容器.appendChild(结果)

def 处理办公正文(window,属性):
    '按转换结果画出状态或 PDF 子槽。有 parent 就挂上去'
    if not _键齐(属性) or '组件' not in 属性:
        return None
    文档=window.document
    if 文档.getElementById('办公正文样式') is None:
        样式=文档.createElement('style')
        样式.id='办公正文样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    组件=属性['组件']
    组件._确保加载()
    模型=Office正文(属性)
    if 模型 is None:
        return None
    if 模型['kind']=='office-loading':
        载=加载指示器({'window':window,'label':模型['label']}).渲染()
        if 'parent' in 属性:
            属性['parent'].appendChild(载)
        return 载
    if 模型['kind']=='office-failed':
        地址=属性['resourceAddress'] if 'resourceAddress' in 属性 else ''
        内容=属性['content'] if 'content' in 属性 else None
        重载=内容['reload'] if isinstance(内容,dict) and 'reload' in 内容 else None
        空=文档.createElement('div')
        空.className='empty'
        图标=文件类型图标({'path':地址 if isinstance(地址,str) else '','size':36,'window':window}).渲染()
        if getattr(图标,'tagName',None) is not None or getattr(图标,'nodeType',None) is not None:
            空.appendChild(图标)
        讯=文档.createElement('div')
        讯.textContent=模型['message']
        空.appendChild(讯)
        if 重载 is not None:
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent=模型['retry']
            def 点重载(事件,回调=重载):
                '再转一次'
                回调()
            钮.addEventListener('click',点重载)
            空.appendChild(钮)
        if 'parent' in 属性:
            属性['parent'].appendChild(空)
        return 空
    体=文档.createElement('div')
    体.className='body'
    提示=模型['fontNotice']
    if isinstance(提示,dict):
        条=字体提示条({
            'fonts':提示['fonts'],
            't':属性['t'],
            'sourceVersion':提示.get('sourceVersion'),
            'window':window,
        })
        节点=条.渲染()
        if 节点 is not None:
            体.appendChild(节点)
    数据=模型['pdf']['data'] if isinstance(模型['pdf'],dict) else None
    if isinstance(数据,bytearray):
        数据=bytes(数据)
    _挂上(体,属性['renderSlot']('sidebar.right.tab.document.office.pdf',{
        'resourceAddress':属性['resourceAddress'],
        'content':{'kind':'bytes','data':数据},
        'wrap':属性.get('wrap') is True,
        'addResource':属性.get('addResource'),
        'setResources':属性.get('setResources'),
        'window':window,
    },{
        'entryKey':'@deepseek-ai/dsh-client-ui-sidebar-documentpreview/office',
        'hookContext':属性['useTabInfo'],
    }))
    if 'parent' in 属性:
        属性['parent'].appendChild(体)
    return 体


class 办公正文:
    'Office 转换中的加载、失败重试与 PDF 结果'

    def __init__(自身,属性):
        '记下正文席 props。有 window 且键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已加载=None
        自身.根=None
        if _键齐(自身.属性) and 'window' in 自身.属性:
            自身.渲染()

    def _确保加载(自身):
        '修订尚未结算时请 Host 转一次，同一修订不重复发起'
        属性=自身.属性
        内容=属性['content']
        if not isinstance(内容,dict) or 内容.get('kind')!='renderer':
            return
        标签=属性['useTabInfo']()['tab']
        修订=内容.get('revision')
        信号=标签.get('signal') if isinstance(标签,dict) else None
        if 信号 is not None and 信号.is_set():
            return
        键=(标签.get('id') if isinstance(标签,dict) else None,修订)
        if 自身.已加载==键:
            return
        持有=属性['useStore'](lambda 状态:状态['byTab'].get(标签['id']) if isinstance(状态,dict) and isinstance(状态.get('byTab'),dict) else None)
        if isinstance(持有,dict) and 持有.get('revision')==修订 and ('file' in 持有 or 持有.get('failure') is not None):
            自身.已加载=键
            return
        已载=内容['loaded'] if 'loaded' in 内容 and callable(内容['loaded']) else (lambda 版本: None)
        失败=内容['failed'] if 'failed' in 内容 and callable(内容['failed']) else (lambda: None)
        自身.已加载=键
        属性['load'](标签['id'],修订,宿主文件(属性['resourceAddress']),信号,已载,失败)

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
        自身.根=处理办公正文(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
