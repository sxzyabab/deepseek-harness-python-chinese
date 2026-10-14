from ..聊天.消息项 import 打开列

__all__=['性能用量行']

性能用量选项=(
    {'id':'compact','label':'settings.performance.compact'},
    {'id':'detailed','label':'settings.performance.detailed'},
)

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键

def 取当前(值):
    '选择器原样返回'
    return 值

def 读快照(存储):
    '字典面或对象面都读当前值'
    if 存储 is None:
        return None
    取=存储['getSnapshot'] if isinstance(存储,dict) and 'getSnapshot' in 存储 else getattr(存储,'getSnapshot',None)
    return 取() if 取 is not None else None

class 性能用量行:
    '选择性能与用量信息的详细程度'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '标题、说明与模式选择'
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 else 恒等翻译
        钩=属性['hooks'] if 'hooks' in 属性 and 属性['hooks'] is not None else {}
        用=属性['usePerformanceUsage'] if 'usePerformanceUsage' in 属性 else None
        存储=钩['performanceUsage'] if 'performanceUsage' in 钩 else None
        模式='detailed'
        选出=None
        if 用 is not None:
            选出=用(取当前)
        elif 存储 is not None:
            选出=读快照(存储)
        if isinstance(选出,str) and 选出!='':
            模式=选出
        选项表={}
        for 项 in 性能用量选项:
            选项表[项['id']]=翻译(项['label'])
        写入=属性['setPerformanceUsage'] if 'setPerformanceUsage' in 属性 else None
        def 改(事件):
            '写回明细偏好'
            if 写入 is None:
                return
            写入(事件.value)
        with 打开列(自身,'性能用量行'):
            界面.label(翻译('settings.performance.title')).classes('标题')
            界面.label(翻译('settings.performance.description')).classes('设置说明')
            界面.select(选项表,value=模式,on_change=改).classes('性能用量')

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)
        自身.渲染()
