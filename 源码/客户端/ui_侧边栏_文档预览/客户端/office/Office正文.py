'Office 拥有源加载、转换失败与缺字体提示，环绕共享 PDF 视图'
from nicegui import ui as 界面
from ....ui_基础界面组件.文件类型图标 import 文件类型图标
from ..加载指示器 import 加载状态
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

__all__=['Office正文','办公正文','样式表']

样式表='''
.body{display:flex;flex-direction:column;height:100%;min-height:0}
'''
界面.add_css(样式表,shared=True)

def Office正文(属性):
    '加载一次 Office 修订并保留至标签关闭。属性为合成 props'
    标签信息=属性['useTabInfo']()#标签信息
    标签=标签信息['tab']#标签
    保留标签=属性['retainTab']#保留
    资源地址=属性['resourceAddress']#地址
    翻译=属性['t']#翻译
    内容=属性['content']#内容
    请求=内容 if 内容.get('kind')=='renderer' else None#渲染器请求
    if 请求 is None:#非渲染器
        return None#空
    修订=请求.get('revision')#修订
    持有=属性['useStore'](lambda 状态:状态['byTab'].get(标签['id']))#持有
    视图=持有 if 持有 is not None and 持有.get('revision')==修订 else None#匹配视图
    保留标签(标签['id'],标签.get('signal'))#保留
    if 视图 is not None and 视图.get('failure') is not None:#失败
        return {'kind':'office-failed','code':视图['failure']['code'],'message':视图['failure']['message'],'retry':翻译('retry')}#失败面
    if 视图 is None or 'file' not in 视图:#加载中
        return {'kind':'office-loading','label':翻译('loading')}#加载
    文件=视图['file']#文件
    return {#成功面
        'kind':'office-body',
        'fontNotice':字体提示({'resourceAddress':资源地址,'sourceVersion':文件.get('version'),'fonts':文件.get('missingFonts',[]),'t':翻译}),
        'pdf':{'kind':'bytes','data':文件.get('data')},
    }#结束


class 办公正文:
    'Office 转换中的加载、失败重试与 PDF 结果'

    def __init__(自身,属性):
        '记下正文席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已加载=None
        if _键齐(自身.属性):
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

    def 渲染(自身):
        '按转换结果画出状态或 PDF 子槽'
        if not _键齐(自身.属性):
            return
        自身._确保加载()
        模型=Office正文(自身.属性)
        if 模型 is None:
            return
        if 模型['kind']=='office-loading':
            加载状态(模型['label']).渲染()
            return
        if 模型['kind']=='office-failed':
            地址=自身.属性['resourceAddress'] if 'resourceAddress' in 自身.属性 else ''
            内容=自身.属性['content'] if 'content' in 自身.属性 else None
            重载=内容['reload'] if isinstance(内容,dict) and 'reload' in 内容 else None
            with 界面.column().classes('empty'):
                文件类型图标({'path':地址 if isinstance(地址,str) else '','size':36}).渲染()
                界面.label(模型['message'])
                if 重载 is not None:
                    界面.button(模型['retry'], on_click=重载)
            return
        with 界面.column().classes('body'):
            提示=模型['fontNotice']
            if isinstance(提示,dict):
                字体提示条({
                    'fonts':提示['fonts'],
                    't':自身.属性['t'],
                    'sourceVersion':提示.get('sourceVersion'),
                }).渲染()
            数据=模型['pdf']['data'] if isinstance(模型['pdf'],dict) else None
            if isinstance(数据,bytearray):
                数据=bytes(数据)
            自身.属性['renderSlot']('sidebar.right.tab.document.office.pdf',{
                'resourceAddress':自身.属性['resourceAddress'],
                'content':{'kind':'bytes','data':数据},
                'wrap':自身.属性.get('wrap') is True,
                'addResource':自身.属性.get('addResource'),
                'setResources':自身.属性.get('setResources'),
            },{
                'entryKey':'@deepseek-ai/dsh-client-ui-sidebar-documentpreview/office',
                'hookContext':自身.属性['useTabInfo'],
            })

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()
