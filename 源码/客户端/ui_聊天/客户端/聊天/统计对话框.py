
from nicegui import ui as 界面
from ..文案 import 中文

__all__=['测量样式','面板边距','面板间隙','统计对话框席','构造统计对话框席']#仅中文公开名

面板边距=12#视口边距（与 Menu 门户边距一致）
面板间隙=8#触发器顶边与面板底边之间的间距

# 未放置的门户面板：隐藏但仍参与布局，供钳制测量真实尺寸
测量样式={'visibility':'hidden','left':0,'top':0}#测量遍样式

class 统计对话框席:
    '单个统计对话框的打开态、引用与钳制后的放置'

    def __init__(自身,受控=None):
        '受控为可选 dict，含 open/setOpen；给出时席位读写该态而非自持'
        自身._自持打开=False#自持打开态
        自身._受控=受控#外部互斥槽
        自身.根引用=None#触发根引用
        自身.面板引用=None#面板引用
        自身.放置=None#钳制后放置样式；None 时用测量样式
        自身.对话框=None#NiceGUI 对话框

    def _有效打开(自身):
        '有效打开态'
        if 自身._受控 is not None and 'open' in 自身._受控:#受控
            return bool(自身._受控['open'])#外部
        return 自身._自持打开#自持

    def _设打开(自身,打开):
        '设置打开态'
        if 自身._受控 is not None and 'setOpen' in 自身._受控:#受控
            自身._受控['setOpen'](bool(打开))#外部
        else:
            自身._自持打开=bool(打开)#自持
        if 自身.对话框 is None:
            return
        if bool(打开):
            自身.对话框.open()
            return
        自身.对话框.close()

    @property
    def 打开(自身):
        '是否打开'
        return 自身._有效打开()#有效

    @打开.setter
    def 打开(自身,值):
        '设置是否打开'
        自身._设打开(值)#委托

    def 设打开(自身,打开):
        '设置打开（供外点关闭与 Escape）'
        自身._设打开(打开)#委托

    def 切换(自身):
        '翻转开合'
        自身._设打开(not 自身._有效打开())#翻

    def 外点关闭(自身):
        '外点 pointerdown 关闭（门户面板算内部；由宿主在指针事件上调用）'
        if 自身._有效打开():#打开中
            自身._设打开(False)#关

    def Escape关闭(自身):
        'Escape 关闭；仅打开时由宿主挂键监听后调用'
        if 自身._有效打开():#打开中
            自身._设打开(False)#关

    def 面板样式(自身):
        '门户面板样式：已放置用放置，否则测量样式'
        return 自身.放置 if 自身.放置 is not None else 测量样式#铺样式

    def 渲染(自身):
        '画出统计对话框，并按打开态显隐。'
        if 自身.对话框 is None:
            with 界面.dialog() as 对话框:
                with 界面.card().classes('统计对话框').style(f'margin:{面板边距}px'):
                    界面.label(中文['stats.dialog.title']).classes('标题')
                    界面.label(中文['stats.dialog.usageTitle'])
                    界面.label(中文['stats.dialog.llmTime'])
                    界面.label(中文['stats.dialog.toolTime'])
                    界面.label(中文['stats.dialog.ttft'])
                    界面.label(中文['stats.dialog.speed'])
                    def 关闭():
                        '关掉统计对话框。'
                        自身.设打开(False)
                    界面.button(中文['details.close'],on_click=关闭)
            def 被隐藏():
                '外点或 Escape 后只改打开态，避免再关一次。'
                if 自身._有效打开() is not True:
                    return
                if 自身._受控 is not None and 'setOpen' in 自身._受控:
                    自身._受控['setOpen'](False)
                    return
                自身._自持打开=False
            对话框.on('hide',被隐藏)
            自身.对话框=对话框
            自身.根引用=对话框
            自身.面板引用=对话框
        if 自身._有效打开():
            自身.对话框.open()

    def __call__(自身,受控=None):
        '可调用席位：可选刷新受控槽后回渲染'
        if 受控 is not None:
            自身._受控=受控#刷
        自身.渲染()#画

def 构造统计对话框席(受控=None):
    """一个锚定触发器的对话框席位：打开态、视口钳制放置、外点关闭。

    受控为可选 dict（open/setOpen），便于兄弟对话框共享互斥槽。
    返回席位；将 pos ?? 测量样式 铺到门户面板上
    """
    return 统计对话框席(受控)#席位
