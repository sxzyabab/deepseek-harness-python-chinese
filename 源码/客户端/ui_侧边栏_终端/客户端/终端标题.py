from nicegui import ui as 界面
from ..异常 import 页面失败文案
from .终端图标 import 终端图标

__all__=['终端标题']

样式表='''
.dsh-term-title-row{display:flex;align-items:center;gap:6px;min-width:0}
.dsh-term-title{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dsh-term-name{width:120px;min-width:48px;max-width:100%;padding:0 4px;color:inherit;font:inherit;background:var(--dsw-alias-bg-l1);border:0.5px solid var(--dsw-alias-border-l3);border-radius:var(--dsw-radius-sm);outline:none}
'''
界面.add_css(样式表,shared=True)

def _引号(文本):
    '放进属性时转掉引号和尖括号'
    return str(文本).replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')

def _键齐(属性):
    '页签、文案、终端和模型都在才画'
    return isinstance(属性,dict) and 'useTabInfo' in 属性 and 't' in 属性 and 'useTerminal' in 属性 and 'view' in 属性

class 终端标题:
    '双击就地改名'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.编辑中=False
        自身.已取消=False
        自身.根=None
        if _键齐(自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 当前标题(自身):
        '优先模型标题，否则页签标题'
        标签=自身.属性['useTabInfo']()['tab']
        def 取标题(状态):
            'info.title 或 title'
            if 状态 is None or not isinstance(状态,dict):
                return None
            信息=状态['info'] if 'info' in 状态 and isinstance(状态['info'],dict) else None
            if 信息 is not None and 'title' in 信息 and 信息['title'] is not None:
                return 信息['title']
            if 'title' in 状态:
                return 状态['title']
            return None
        名=自身.属性['useTerminal'](标签['id'],取标题)
        if 名 is None:
            return 标签['title'] if isinstance(标签,dict) and 'title' in 标签 else ''
        return 名

    def 开始改名(自身):
        '进入编辑'
        自身.已取消=False
        自身.编辑中=True

    def 提交改名(自身,下一):
        '非空且不同则 rename。Escape 之后的失焦丢弃'
        自身.编辑中=False
        修剪=下一.strip() if isinstance(下一,str) else ''
        标题=自身.当前标题()
        if 自身.已取消:
            return
        if 修剪=='' or 修剪==标题:
            return
        标签=自身.属性['useTabInfo']()['tab']
        自身.属性['view'](标签['id']).rename(修剪)

    def _腾出(自身):
        '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句'
        旧=自身.根
        if 旧 is None:
            return None
        try:
            旧.clear()
        except Exception as 错:
            自身.根=None
            return 页面失败文案(错)
        return None

    def 渲染(自身):
        '图标加标题；双击进入改名，失焦提交，Escape 取消'
        if not _键齐(自身.属性):
            return
        清除失败=自身._腾出()
        if 自身.根 is None:
            自身.根=界面.row().classes('dsh-term-title-row')
        翻译=自身.属性['t']
        标题=自身.当前标题()
        展示=标题 if isinstance(标题,str) else ''
        with 自身.根:
            if isinstance(清除失败,str) and 清除失败!='':
                界面.label(清除失败)
            终端图标().渲染()
            if 自身.编辑中:
                框=界面.input(value=展示).props('maxlength=120 aria-label="'+_引号(翻译('rename'))+'"').classes('dsh-term-name')
                def 按键(事件):
                    'Escape 取消，Enter 提交'
                    参数=事件.args if hasattr(事件,'args') else None
                    键=参数['key'] if isinstance(参数,dict) and isinstance(参数.get('key'),str) else getattr(事件,'key',None)
                    if 键=='Escape':
                        自身.已取消=True
                        自身.编辑中=False
                        自身.渲染()
                    elif 键=='Enter':
                        自身.提交改名(框.value if isinstance(框.value,str) else '')
                        自身.渲染()
                def 失焦():
                    '失焦提交当前输入'
                    自身.提交改名(框.value if isinstance(框.value,str) else '')
                    自身.渲染()
                框.on('keydown', 按键)
                框.on('blur', lambda _: 失焦())
            else:
                def 改名():
                    '双击进入编辑'
                    自身.开始改名()
                    自身.渲染()
                界面.label(展示).classes('dsh-term-title').on('dblclick', lambda _: 改名())

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
