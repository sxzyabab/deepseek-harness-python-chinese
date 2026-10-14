'删除结果的应用级横幅'
from nicegui import ui as 界面
from ..异常 import 页面失败文案
from ...存储 import 创建快照存储

__all__=['创建删除提示源','删除提示']

class 删除提示:
    'shell.overlay：成功或失败横幅；没有通知时不画'
    def __init__(自身,属性=None):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 'useToast' in 自身.属性 and 'dismiss' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 确保订阅(自身):
        '通知变化时重画'
        if getattr(自身,'_已订',False):
            return
        用=自身.属性['useToast'] if 'useToast' in 自身.属性 else None
        订=getattr(用,'_subscribe',None)
        if not callable(订):
            return
        自身._已订=True
        def 变(*_参数):
            '重画横幅'
            if getattr(自身,'_壳',None) is not None:
                自身.重画()
        订(变)

    def 渲染(自身):
        '先占一个壳，再按当前通知画'
        自身.确保订阅()
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('schedule-delete-toast')
        自身.重画()

    def 重画(自身):
        '成功条或警告条'
        壳=getattr(自身,'_壳',None)
        if 壳 is None:
            return
        壳.clear()
        用=自身.属性['useToast'] if 'useToast' in 自身.属性 else None
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else (lambda 键,_参数=None:键)
        if not callable(用):
            return
        try:
            通知=用(lambda 当前:当前)
        except Exception:
            return
        if not isinstance(通知,dict) or 'kind' not in 通知:
            return
        收起=自身.属性['dismiss'] if 'dismiss' in 自身.属性 and callable(自身.属性['dismiss']) else (lambda:None)
        文=翻译('toast.deleted' if 通知['kind']=='deleted' else 'toast.deleteFailed')
        with 壳:
            with 界面.row().classes('schedule-toast'):
                if 通知['kind']!='deleted':
                    界面.icon('warning', size='18px')
                界面.label(文)
                界面.button(on_click=收起).props('icon=close flat round')

    def __call__(自身,属性=None):
        '有新 props 则更新后再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def 创建删除提示源():
    '一份快照存储；pending 不发横幅'
    仓=创建快照存储(None)
    序号=[0]
    def 报告(结局):
        'deleted / failed 各发一条；pending 忽略'
        if 结局=='pending':
            return
        序号[0]+=1
        仓.set({'kind':'deleted' if 结局=='deleted' else 'deleteFailed','seq':序号[0]})
    def 收起():
        '关掉当前横幅'
        仓.set(None)
    return {'hooks':{'toast':仓},'report':报告,'dismiss':收起}
