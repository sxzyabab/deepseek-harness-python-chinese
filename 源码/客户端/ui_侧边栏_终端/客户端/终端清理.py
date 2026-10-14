import importlib.resources as 包资源
from nicegui import ui as 界面
from ..异常 import 去掉敏感,页面失败文案

__all__=['终端清理']

def _读样式():
    '读同目录清理样式。打不开时只报样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath('终端清理.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

样式表=_读样式()
界面.add_css(样式表,shared=True)

def _键齐(属性):
    '失败列表和文案都在才画'
    return isinstance(属性,dict) and 'useCloseFailures' in 属性 and 't' in 属性

class 终端清理:
    '失败清理可重试，不重建标签'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if _键齐(自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 重试关闭(自身,标识):
        '请求重试结束'
        自身.属性['retryClose'](标识)

    def _失败表(自身):
        '读当前失败列表'
        def 取失败(值):
            '交还原列表'
            return 值
        值=自身.属性['useCloseFailures'](取失败)
        if isinstance(值,list):
            return 值
        return []

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
        '每条失败通知带一句说明和重试。说明去掉绝对路径'
        if not _键齐(自身.属性):
            return
        清除失败=自身._腾出()
        失败表=自身._失败表()
        if len(失败表)==0 and not isinstance(清除失败,str):
            return
        if 自身.根 is None:
            自身.根=界面.element('div').classes('dsh-term-clean-stack')
        翻译=自身.属性['t']
        with 自身.根:
            if isinstance(清除失败,str) and 清除失败!='':
                界面.label(清除失败).classes('dsh-term-clean-notice')
            for 失败 in 失败表:
                if not isinstance(失败,dict) or 'id' not in 失败:
                    continue
                标识=失败['id']
                标题=失败['title'] if 'title' in 失败 else ''
                说明=去掉敏感(失败['message']) if 'message' in 失败 else ''
                def 点重试(当前=标识):
                    '重试这一条'
                    自身.重试关闭(当前)
                with 界面.element('div').classes('dsh-term-clean-notice'):
                    界面.label(翻译('cleanupFailed',{'title':标题,'message':说明}))
                    界面.button(翻译('retry'), on_click=点重试).props('flat no-caps')

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
