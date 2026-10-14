from nicegui import ui as 界面
from ...异常 import 页面失败文案
from ..聊天.消息项 import 打开列

__all__=['链接打开行']

链接打开选项=(
    {'id':'sidebar','label':'settings.links.sidebar'},
    {'id':'new-tab','label':'settings.links.newTab'},
)

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

class 链接打开行:
    '内建浏览器可用时，选择对话链接打开位置'
    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}

    def 渲染(自身):
        '无内建浏览器则不画'
        属性=自身.属性
        可用=属性['browserAvailable'] if 'browserAvailable' in 属性 else None
        钩=属性['hooks'] if 'hooks' in 属性 and 属性['hooks'] is not None else {}
        if 可用 is None and 'browserAvailable' in 钩:
            可用=钩['browserAvailable']
        有浏览器=可用() if callable(可用) else 可用 is True
        if 有浏览器 is not True:
            if 自身.根 is not None:
                try:
                    自身.根.clear()
                    自身.根.set_visibility(False)
                except Exception as 错误:
                    自身.根=None
                    界面.label(页面失败文案(错误))
            return
        翻译=属性['t'] if 't' in 属性 else 恒等翻译
        用=属性['useLinkOpening'] if 'useLinkOpening' in 属性 else None
        存储=钩['linkOpening'] if 'linkOpening' in 钩 else None
        去向='sidebar'
        选出=None
        if 用 is not None:
            选出=用(取当前)
        elif 存储 is not None:
            选出=读快照(存储)
        if isinstance(选出,str) and 选出!='':
            去向=选出
        选项表={}
        for 项 in 链接打开选项:
            选项表[项['id']]=翻译(项['label'])
        写入=属性['setLinkOpening'] if 'setLinkOpening' in 属性 else None
        def 改(事件):
            '写回打开位置'
            if 写入 is None:
                return
            写入(事件.value)
        with 打开列(自身,'链接打开行'):
            自身.根.set_visibility(True)
            界面.label(翻译('settings.links.title')).classes('标题')
            界面.label(翻译('settings.links.description')).classes('设置说明')
            界面.select(选项表,value=去向,on_change=改).classes('链接打开')

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)
        自身.渲染()
