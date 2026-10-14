import importlib.resources as 包资源
from nicegui import ui as 界面
from ..异常 import 页面失败文案
from .终端图标 import 终端引导图标

__all__=['终端引导']

def _读样式():
    '读同目录引导样式。打不开时只报样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath('终端引导.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

样式表=_读样式()
界面.add_css(样式表,shared=True)

def _引号(文本):
    '放进属性时转掉引号和尖括号'
    return str(文本).replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')

def _键齐(属性):
    '文案、标题和页签都在才画'
    return isinstance(属性,dict) and 't' in 属性 and 'title' in 属性 and 'useTabInfo' in 属性

class 终端引导:
    '卡片启动记住的壳，菜单另选壳'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False
        自身.尝试=0
        自身.菜单={'phase':'loading'}
        自身.已读=False
        自身.根=None
        自身.菜单控件=None
        自身.失败=None
        if _键齐(自身.属性):
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 切菜单(自身):
        '打开时重置为 loading，并重画'
        if 自身.打开:
            自身.打开=False
        else:
            自身.菜单={'phase':'loading'}
            自身.已读=False
            自身.打开=True
        自身.渲染()

    def 关菜单(自身):
        '关上菜单并重画'
        自身.打开=False
        自身.渲染()

    def 选壳(自身,路径):
        '失败则重试；否则记住并打开标签'
        if 自身.菜单.get('phase')=='failed':
            自身.菜单={'phase':'loading'}
            自身.已读=False
            自身.尝试+=1
            自身.渲染()
            return
        try:
            自身.属性['selectShell'](路径)
            标签=自身.属性['useTabInfo']()['tab']
            标签['actions'].openTab('terminal',{'replaceTab':True,'params':{'shellPath':路径}})
        except Exception as 错:
            自身.失败=页面失败文案(错)
            自身.渲染()
            return
        自身.失败=None
        自身.打开=False
        自身.渲染()

    def 开终端(自身):
        '替换当前页签为终端。失败留在卡片上，说明不含绝对路径'
        try:
            标签=自身.属性['useTabInfo']()['tab']
            标签['actions'].openTab('terminal',{'replaceTab':True})
        except Exception as 错:
            自身.失败=页面失败文案(错)
            自身.渲染()
            return
        自身.失败=None

    def 菜单项(自身):
        '按阶段投影项'
        翻译=自身.属性['t']
        阶段=自身.菜单.get('phase')
        if 阶段=='ready':
            项表=[]
            选择=自身.菜单.get('choices') if isinstance(自身.菜单.get('choices'),dict) else {}
            壳表=选择.get('shells') if isinstance(选择.get('shells'),list) else []
            for 壳 in 壳表:
                if isinstance(壳,dict) and isinstance(壳.get('path'),str):
                    名=壳.get('name') if isinstance(壳.get('name'),str) else 壳['path']
                    项表.append({'id':壳['path'],'label':名})
            return 项表
        if 阶段=='loading':
            return [{'id':'loading','label':翻译('shellLoading'),'disabled':True}]
        说明=自身.菜单.get('message') if isinstance(自身.菜单.get('message'),str) else ''
        return [
            {'id':'error','label':翻译('failed',{'message':说明}),'disabled':True},
            {'id':'retry','label':翻译('retry')},
        ]

    def 读壳(自身):
        '菜单打开时读取宿主壳列表。失败记成菜单说明，不含绝对路径'
        if 自身.打开 is not True or 自身.已读 or 'loadShells' not in 自身.属性:
            return
        自身.已读=True
        try:
            结果=自身.属性['loadShells'](None)
        except Exception as 错:
            自身.菜单={'phase':'failed','message':页面失败文案(错)}
            return
        if isinstance(结果,dict) and isinstance(结果.get('shells'),list):
            自身.菜单={'phase':'ready','choices':结果}
            return
        自身.菜单={'phase':'failed','message':''}

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
        '主按钮打开终端，菜单另选壳'
        if not _键齐(自身.属性):
            return
        自身.读壳()
        清除失败=自身._腾出()
        属性=自身.属性
        翻译=属性['t']
        标题=属性['title'] if isinstance(属性['title'],str) else ''
        说明=属性['description'] if 'description' in 属性 and isinstance(属性['description'],str) else None
        种类=属性['kind'] if 'kind' in 属性 and isinstance(属性['kind'],str) else ''
        尺寸=22 if 说明 is None else 26
        if 自身.根 is None:
            自身.根=界面.element('div').classes('dsh-term-guide')
        if 种类!='' and all(字.isalnum() or 字 in '-_' for 字 in 种类):
            自身.根.props('data-sidebar-right-guide-entry='+种类)
        项表=自身.菜单项()
        if len(项表)==0:
            项表=[{'id':'empty','label':翻译('shellEmpty'),'disabled':True}]
        with 自身.根:
            if isinstance(清除失败,str) and 清除失败!='':
                界面.label(清除失败)
            if isinstance(自身.失败,str) and 自身.失败!='':
                界面.label(自身.失败)
            无障碍=标题 if 说明 is None or 说明=='' else 标题+' '+说明
            界面.button('', on_click=自身.开终端).props('flat aria-label="'+_引号(无障碍)+'"').classes('dsh-term-guide-main')
            with 界面.element('span').classes('dsh-term-guide-icon'):
                终端引导图标({'size':尺寸}).渲染()
            with 界面.column().classes('dsh-term-guide-text'):
                with 界面.row().classes('dsh-term-guide-title-row'):
                    界面.label(标题).classes('dsh-term-guide-title')
                    with 界面.element('div').classes('dsh-term-guide-menu'):
                        触发=界面.button(icon='expand_more', on_click=自身.切菜单).props('flat dense round aria-label="'+_引号(翻译('shell'))+'"').classes('dsh-term-guide-trigger')
                        with 触发:
                            菜单=界面.menu()
                            自身.菜单控件=菜单
                            with 菜单:
                                for 项 in 项表:
                                    _画菜单项(自身,项)
                        if 自身.打开:
                            _打开菜单(菜单)
                if 说明 is not None and 说明!='':
                    界面.label(说明).classes('dsh-term-guide-desc')
            快捷=_快捷文(属性)
            if 快捷!='':
                界面.label(快捷).classes('dsh-term-guide-shortcut')

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def _打开菜单(菜单):
    '展开壳菜单。有 open 就调用，否则把值写成打开。失败留一句说明'
    try:
        打开=getattr(菜单,'open',None)
        if callable(打开):
            打开()
            return
        设值=getattr(菜单,'set_value',None)
        if callable(设值):
            设值(True)
    except Exception as 错:
        界面.label(页面失败文案(错))

def _画菜单项(引导,项):
    '一行壳名。禁用项不可点；重试项重新读取'
    标识=项.get('id')
    文=项.get('label') if isinstance(项.get('label'),str) else ''
    禁=项.get('disabled') is True
    def 点(路径=标识,禁用=禁):
        '记住所选壳并打开；失败项则重读'
        if 禁用:
            return
        if 路径=='retry':
            引导.已读=False
            引导.菜单={'phase':'loading'}
            引导.尝试+=1
            引导.渲染()
            return
        引导.选壳(路径)
    钮=界面.menu_item(文, on_click=点)
    if 禁:
        钮.disable()

def _快捷文(属性):
    '有 useShortcuts 时取出新建终端的按键文案'
    取=属性.get('useShortcuts') if isinstance(属性,dict) else None
    if not callable(取):
        return ''
    def 挑(条目表):
        '找 terminal.new'
        if isinstance(条目表,dict):
            内=条目表.get('catalog')
            条目表=内 if isinstance(内,list) else []
        if not isinstance(条目表,(list,tuple)):
            return None
        for 条 in 条目表:
            if isinstance(条,dict) and 条.get('id')=='terminal.new':
                return 条
        return None
    try:
        条=取(挑)
    except Exception as 错:
        return 页面失败文案(错)
    if not isinstance(条,dict):
        return ''
    键表=条.get('keys')
    if not isinstance(键表,(list,tuple)) or len(键表)==0:
        return ''
    段=[]
    for 键 in 键表:
        if isinstance(键,str) and 键!='':
            段.append(键)
        elif isinstance(键,dict) and isinstance(键.get('label'),str) and 键['label']!='':
            段.append(键['label'])
    return ' '.join(段)
