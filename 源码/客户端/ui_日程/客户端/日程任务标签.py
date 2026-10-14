'右侧栏里一条任务的正文'
from nicegui import ui as 界面
from ..异常 import 页面失败文案
from .日历图标 import 日历图标
from .目录反馈 import 目录反馈
from .任务详情 import 任务详情
from .任务标签目标 import 解析任务标签目标

__all__=['日程任务标签']

def 取(对象,键):
    '字典或对象'
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else None
    return getattr(对象,键,None)

class 日程任务标签:
    '槽位只调用构造。找不到任务时显示缺失或加载'
    def __init__(自身,属性=None):
        '记下基准读取序号。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.基准=None
        if 'useTabInfo' in 自身.属性 and 'useCatalog' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '详情或缺失说明'
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        标签=None
        用标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None
        if callable(用标签):
            try:
                信息=用标签(lambda 当前:当前)
                标签=取(信息,'tab')
            except Exception:
                标签=None
        绑定=属性['taskBindings'] if 'taskBindings' in 属性 else None
        解析=解析任务标签目标(属性['sessionId'] if 'sessionId' in 属性 else None,标签 if 标签 is not None else {},绑定)
        参数=解析['params']
        目录=自身._目录()
        记录=None
        if isinstance(参数,dict):
            for 项 in 目录['records'] if 'records' in 目录 and isinstance(目录['records'],list) else []:
                if isinstance(项,dict) and 项.get('id')==参数.get('id'):
                    记录=项
                    break
        if 自身.基准 is None:
            自身.基准=目录['readRequest'] if 'readRequest' in 目录 else 0
        已答='settled' in 目录 and 目录['settled'] is True and 目录.get('readSettled',0)>自身.基准
        if 记录 is None and 已答 is False:
            重试=属性['onRetry'] if 'onRetry' in 属性 and callable(属性['onRetry']) else None
            if 重试 is not None:
                重试(自身.基准)
        if isinstance(参数,dict) and 解析['navigated'] is True and 绑定 is not None and 标签 is not None:
            绑定.写入(属性.get('sessionId'),{'id':取(标签,'id'),'kind':取(标签,'kind'),'contentId':取(标签,'contentId')},参数)
        if 记录 is None and 解析['recovered'] is not None and 解析['navigated'] is False and 已答 and 绑定 is not None and 标签 is not None:
            绑定.忘记(属性.get('sessionId'),{'id':取(标签,'id'),'kind':取(标签,'kind'),'contentId':取(标签,'contentId')})
        with 界面.column().classes('schedule-task-tab'):
            if 记录 is None:
                if 已答:
                    日历图标({'size':24}).渲染()
                    界面.label(翻译('detail.missing'))
                else:
                    待定=目录.get('status')=='ready' and 已答 is False
                    目录反馈({'status':'loading' if 待定 else 目录.get('status','loading'),'populated':False,'onRetry':属性['onRetry'] if 'onRetry' in 属性 else (lambda *_参数:None),'t':翻译}).渲染()
                return
            def 关掉():
                '目录确认删除后关这个标签'
                动作=取(标签,'actions')
                关=取(动作,'close')
                if callable(关):
                    关()
            任务详情({
                **属性,
                'task':记录,
                'status':目录.get('status','ready'),
                'deleting':目录['deleting'] if 'deleting' in 目录 and isinstance(目录['deleting'],list) else [],
                'authoritative':True,
                'onDeleted':关掉,
                'withinSession':属性.get('sessionId'),
            }).渲染()

    def _目录(自身):
        '读共享目录'
        用=自身.属性['useCatalog'] if 'useCatalog' in 自身.属性 else None
        if not callable(用):
            return {'records':[],'status':'loading','settled':False,'readRequest':0,'readSettled':0,'deleting':[]}
        try:
            值=用(lambda 当前:当前)
        except Exception:
            return {'records':[],'status':'error','settled':False,'readRequest':0,'readSettled':0,'deleting':[]}
        return 值 if isinstance(值,dict) else {'records':[],'status':'error','settled':False,'readRequest':0,'readSettled':0,'deleting':[]}

    def __call__(自身,属性=None):
        '更新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
