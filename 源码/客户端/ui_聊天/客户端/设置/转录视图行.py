
from ..聊天.消息项 import 打开列

__all__=['转录视图行','转录视图选项']#仅中文公开名

转录视图选项=(#可选模式
    {'id':'compact','label':'settings.transcript.compact'},#简洁
    {'id':'standard','label':'settings.transcript.standard'},#标准
    {'id':'detailed','label':'settings.transcript.detailed'},#详细
    {'id':'verbose','label':'settings.transcript.verbose'},#完全展开
)#OPTIONS 结束

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 取当前(值):
    '选择器原样返回'
    return 值#当前

def 读快照(存储):
    '字典面或对象面都读当前值'
    if 存储 is None:
        return None
    取=存储['getSnapshot'] if isinstance(存储,dict) and 'getSnapshot' in 存储 else getattr(存储,'getSnapshot',None)
    return 取() if 取 is not None else None

class 转录视图行:
    '模式选择器结构树'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.打开=False#菜单开合
        自身.根=None#列
        自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '标题 + 下拉'
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用模式=属性['useTranscriptView'] if 'useTranscriptView' in 属性 else None#钩子
        钩=属性['hooks'] if 'hooks' in 属性 and 属性['hooks'] is not None else {}
        存储=钩['transcriptView'] if 'transcriptView' in 钩 else None
        模式='standard'#默认
        选出=None
        if 用模式 is not None:
            选出=用模式(取当前)#当前
        elif 存储 is not None:
            选出=读快照(存储)
        if isinstance(选出,str) and 选出!='':
            模式=选出#当前
        选项表={}
        for 项 in 转录视图选项:#项
            选项表[项['id']]=翻译(项['label'])
        写入=属性['setTranscriptView'] if 'setTranscriptView' in 属性 else None#写入
        def 改模式(事件):
            '把选中的显示模式写回去。'
            if 写入 is None:
                return
            写入(事件.value)
        with 打开列(自身,'转录视图行'):
            界面.label(翻译('settings.transcript.title')).classes('标题')
            界面.label(翻译('settings.transcript.description')).classes('设置说明')
            界面.select(选项表,value=模式,on_change=改模式).classes('转录模式')

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
