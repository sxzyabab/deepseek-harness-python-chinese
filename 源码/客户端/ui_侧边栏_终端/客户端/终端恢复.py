from nicegui import ui as 界面
from ..异常 import 页面失败文案

__all__=['终端恢复']

def _键齐(属性):
    '恢复回调和文案都在才画'
    return isinstance(属性,dict) and 'restore' in 属性 and 't' in 属性

class 终端恢复:
    '显示 Session 时恢复终端；失败给重试'
    def __init__(自身,属性):
        '记下 props。键齐了就恢复，失败时再画重试'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.错误=None
        自身.尝试=0
        自身.存活=True
        自身.根=None
        if _键齐(自身.属性):
            自身.恢复()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 卸载(自身):
        '标死，随后到达的失败不再画'
        自身.存活=False

    def 恢复(自身):
        '失败记下不含绝对路径的说明'
        try:
            自身.属性['restore']()
            if 自身.存活:
                自身.错误=None
        except Exception as 错误:
            if not 自身.存活:
                return
            自身.错误=页面失败文案(错误)
        if 自身.存活:
            自身.渲染()

    def 重试(自身):
        '清错再恢复'
        自身.错误=None
        自身.尝试+=1
        自身.恢复()

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
        '没有失败时不留按钮；失败时给出重试'
        if not _键齐(自身.属性):
            return
        清除失败=自身._腾出()
        if 自身.错误 is None and not isinstance(清除失败,str):
            return
        if 自身.根 is None:
            自身.根=界面.row()
        翻译=自身.属性['t']
        with 自身.根:
            if isinstance(清除失败,str) and 清除失败!='':
                界面.label(清除失败)
            if isinstance(自身.错误,str) and 自身.错误!='':
                界面.button(翻译('retryRecovery'), on_click=自身.重试).props('flat no-caps').tooltip(翻译('recoveryFailed',{'message':自身.错误}))

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
