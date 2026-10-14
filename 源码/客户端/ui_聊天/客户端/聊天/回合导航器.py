
from .消息项 import 打开列,收起列

__all__=['回合导航器','标记间距','轨内边','淡出带']#仅中文公开名

标记间距=10#相邻标记间距
轨内边=6#首末内边
淡出带=24#端蒙版淡出

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 项位样式(索引):
    '自然位置 px'
    return {'--turn-natural-position':f'{索引*标记间距}px'}#位

def 框样式(数量,滚动顶):
    '自然高与滚动'
    return {'--turn-natural-height':f'{(max(0,数量-1)*标记间距)+2*轨内边}px','--turn-rail-inset':f'{轨内边}px','--turn-scroll-top':f'{滚动顶}px'}#框

def 造跳转(导航,目标):
    '闭包固定该项'
    def 跳转():
        '跳到该项'
        导航(目标)#跳
    return 跳转#回调

class 回合导航器:
    '标记列表 + 预览 + 导航回调'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.预览回合=None#预览
        自身.滚动顶=0#顶
        自身.根=None#列

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '轨'
        属性=自身.属性#props
        原始=属性['items'] if 'items' in 属性 and 属性['items'] is not None else []#项
        项列表=list(原始)#项
        活动=属性['activeTurn'] if 'activeTurn' in 属性 else None#活动
        忙=属性['busyTurn'] if 'busyTurn' in 属性 else None#忙
        导航=属性['onNavigate'] if 'onNavigate' in 属性 else None#导航
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        if len(项列表)==0:
            收起列(自身)
            return
        框=框样式(len(项列表),自身.滚动顶)
        with 打开列(自身,'回合导航器'):
            样式段=[]
            for 键,值 in 框.items():
                样式段.append(str(键)+':'+str(值))
            自身.根.style(';'.join(样式段))
            界面.label(翻译('chat.turnNavigation.label')).classes('标题')
            for 索引,项 in enumerate(项列表):#扫
                回合=项['turn'] if 'turn' in 项 else None#回合
                锚=项['anchor'] if 'anchor' in 项 and 项['anchor'] is not None else {}#锚
                锚种=锚['kind'] if 'kind' in 锚 else None#锚种
                跳键='chat.turnNavigation.jumpLoad' if 锚种=='unloaded' else 'chat.turnNavigation.jump'#键
                回调=造跳转(导航,项) if 导航 is not None else None#导航
                提示=项['prompt'] if 'prompt' in 项 else None#提示
                回复=项['response'] if 'response' in 项 else None#回复
                位=项位样式(索引)
                位段=[]
                for 键,值 in 位.items():
                    位段.append(str(键)+':'+str(值))
                按钮=界面.button(翻译('chat.turnNavigation.turn',{'turn':回合}),on_click=回调)
                按钮.style(';'.join(位段))
                按钮.tooltip(翻译(跳键,{'turn':回合}))
                if 回合==活动:
                    按钮.classes(add='活动')
                if 回合==忙:
                    按钮.classes(add='忙碌')
                if 回合==自身.预览回合:
                    按钮.classes(add='预览')
                if 提示 is not None and not (isinstance(提示,str) and 提示==''):
                    界面.label(str(提示)).classes('提示')
                if 回复 is not None and not (isinstance(回复,str) and 回复==''):
                    界面.label(str(回复)).classes('回复')

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
