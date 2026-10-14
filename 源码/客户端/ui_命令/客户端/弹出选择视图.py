from nicegui import ui as 界面
from ...ui_基础界面组件.风险确认 import 风险确认
from ..异常 import 页面失败文案
from .服务 import 分组选项,过滤选项

__all__=['弹出选择视图']

样式表='''
.dsh-cmd-host{position:relative;width:100%}
.dsh-cmd-card{position:absolute;bottom:calc(100% + 4px);left:0;right:0;z-index:100;box-sizing:border-box;display:flex;flex-direction:column;max-width:100%;max-height:320px;overflow:hidden;padding:3px;border:0;background:var(--dsw-specific-menu,var(--dsw-alias-bg-l1));box-shadow:var(--dsw-elevation-prominent);outline:none}
.dsh-cmd-viewport{display:flex;flex-direction:column;min-height:0;overflow-y:auto}
.dsh-cmd-row{display:flex;align-items:center;gap:6px;padding:5px 7px;border-radius:var(--dsw-radius-md);cursor:pointer;font-size:12px;color:var(--dsw-alias-label-primary)}
.dsh-cmd-row-active{background:var(--dsw-alias-interactive-bg-hover)}
.dsh-cmd-label{display:flex;align-items:baseline;gap:4px;flex:0 1 auto;min-width:0}
.dsh-cmd-label-text{min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dsh-cmd-badge{flex:none;color:var(--dsw-alias-label-tertiary);font-size:8px;line-height:10px;font-weight:600}
.dsh-cmd-detail{flex:1;min-width:0;font-size:11px;color:var(--dsw-alias-label-tertiary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dsh-cmd-check{margin-left:auto;color:var(--dsw-alias-label-primary)}
.dsh-cmd-status{padding:7px 8px;font-size:12px;color:var(--dsw-alias-label-tertiary)}
.dsh-cmd-search{margin:2px 2px 3px}
.dsh-cmd-error{display:flex;align-items:center;gap:6px;padding:5px 7px;font-size:11px;color:var(--dsw-alias-state-error-primary)}
.dsh-cmd-error-text{flex:1;overflow:hidden;text-overflow:ellipsis}
.dsh-cmd-group{padding:6px 8px 2px;color:var(--dsw-alias-label-tertiary);font-size:11px;line-height:16px}
'''
界面.add_css(样式表,shared=True)

def _引号(文本):
    '放进属性时转掉引号和尖括号'
    return str(文本).replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')

def _键名(事件):
    '从键盘事件取出 key 和是否按着 Shift'
    参数=事件.args if hasattr(事件,'args') else None
    键=''
    移位=False
    if isinstance(参数,dict):
        if isinstance(参数.get('key'),str):
            键=参数['key']
        移位=参数.get('shiftKey') is True
    elif isinstance(getattr(事件,'key',None),str):
        键=事件.key
    return 键,移位

class 弹出选择视图:
    '斜杠命令的搜索、分组选项和风险确认'
    def __init__(自身,属性):
        '记下叠层 props。槽位只调用构造，有 popup 就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.状态区=None
        自身.列表区=None
        自身._模式=None
        自身._退订=None
        自身._已订=None
        自身._在画=False
        自身._再画=False
        if 'popup' in 自身.属性:
            自身.渲染()

    def _翻译(自身,键,参数=None):
        '缺文案钩子时返回键'
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else None
        if 翻译 is None:
            return 键
        if 参数 is None:
            return 翻译(键)
        return 翻译(键,参数)

    def _弹出(自身):
        '注入的弹出控制器；没有则 None'
        弹出=自身.属性['popup'] if 'popup' in 自身.属性 else None
        return 弹出

    def _订(自身,弹出):
        '状态一变就重画。getSnapshot 和 subscribe 保持这两个名字'
        if 弹出 is 自身._已订:
            return
        if callable(自身._退订):
            自身._退订()
            自身._退订=None
        自身._已订=弹出
        状态=getattr(弹出,'state',None) if 弹出 is not None else None
        订=getattr(状态,'subscribe',None) if 状态 is not None else None
        if not callable(订):
            return
        def 重画():
            '快照变了再画一版。失败留在页面上，说明不含绝对路径'
            try:
                自身.渲染()
            except Exception as 错:
                界面.label(页面失败文案(错))
        自身._退订=订(重画)

    def _腾出(自身):
        '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句'
        旧=自身.根
        if 旧 is None:
            return None
        try:
            旧.clear()
        except Exception as 错:
            自身.根=None
            自身.状态区=None
            自身.列表区=None
            自身._模式=None
            return 页面失败文案(错)
        return None

    def 渲染(自身):
        '未打开时不留卡片；打开时画出搜索和选项'
        if 自身._在画:
            自身._再画=True
            return
        自身._在画=True
        try:
            自身._画出()
        finally:
            自身._在画=False
        if 自身._再画:
            自身._再画=False
            自身.渲染()

    def _画出(自身):
        '按控制器快照画卡片或风险确认'
        弹出=自身._弹出()
        自身._订(弹出)
        if 弹出 is None or not callable(getattr(getattr(弹出,'state',None),'getSnapshot',None)):
            清除失败=自身._腾出()
            if isinstance(清除失败,str) and 清除失败!='':
                界面.label(清除失败)
            return
        态=弹出.state.getSnapshot()
        if not isinstance(态,dict) or 态.get('open') is not True:
            自身._腾出()
            自身._模式=None
            return
        if isinstance(态.get('confirming'),dict):
            自身._画确认(弹出,态)
            return
        自身._画列表(弹出,态)

    def _画确认(自身,弹出,态):
        '风险门打开时只画确认，不画选项列表'
        清除失败=自身._腾出()
        自身._模式='confirm'
        if 自身.根 is None:
            自身.根=界面.column().classes('dsh-cmd-host')
        确认=态['confirming'].get('confirmation') if isinstance(态['confirming'].get('confirmation'),dict) else {}
        with 自身.根:
            if isinstance(清除失败,str) and 清除失败!='':
                界面.label(清除失败)
            def 认(值):
                '记下风险勾选'
                弹出.acknowledge(值)
            def 取消():
                '回到选项列表'
                弹出.cancelConfirmation()
            def 确定():
                '勾选后结算'
                弹出.confirm()
            风险确认({
                'open':True,
                'title':确认.get('title'),
                'description':确认.get('description'),
                'acknowledgeLabel':确认.get('acknowledgeLabel'),
                'cancelLabel':确认.get('cancelLabel'),
                'confirmLabel':确认.get('confirmLabel'),
                'closeLabel':自身._翻译('close'),
                'acknowledged':态.get('acknowledged') is True,
                'onAcknowledgedChange':认,
                'onCancel':取消,
                'onConfirm':确定,
            }).渲染()

    def _画列表(自身,弹出,态):
        '搜索框保持不动，状态区和列表随快照重填'
        if 自身._模式!='list' or 自身.根 is None or 自身.状态区 is None or 自身.列表区 is None:
            清除失败=自身._腾出()
            if 自身.根 is None:
                自身.根=界面.column().classes('dsh-cmd-host')
            自身._模式='list'
            命令=态.get('command') if isinstance(态.get('command'),str) else ''
            with 自身.根:
                if isinstance(清除失败,str) and 清除失败!='':
                    界面.label(清除失败)
                卡=界面.column().classes('dsh-cmd-card')
                卡.props('aria-label="'+_引号(自身._翻译('overlay.aria',{'command':命令}))+'"')
                with 卡:
                    占位=自身._占位(态)
                    框=界面.input(
                        value=态.get('search') if isinstance(态.get('search'),str) else '',
                        placeholder=占位,
                        on_change=lambda 事件: 自身._改搜索(弹出,事件),
                    ).props('aria-label="'+_引号(自身._翻译('search.aria'))+'"').classes('dsh-cmd-search')
                    if 态.get('submitting') is True:
                        框.props('readonly')
                    框.on('keydown', lambda 事件: 自身._按键(弹出,事件))
                    自身.状态区=界面.column()
                    自身.列表区=界面.column().classes('dsh-cmd-viewport')
                    自身.列表区.props('role=listbox aria-label="'+_引号(自身._翻译('listbox.aria',{'command':命令}))+'"')
        自身._填状态(弹出,态)
        自身._填列表(弹出,态)

    def _占位(自身,态):
        '命令自带占位优先，否则用通用文案'
        标签=态.get('searchLabels') if isinstance(态.get('searchLabels'),dict) else None
        if isinstance(标签,dict) and isinstance(标签.get('placeholder'),str) and 标签['placeholder']!='':
            return 标签['placeholder']
        return 自身._翻译('search.placeholder')

    def _空文(自身,态):
        '还没选项和过滤后没有结果可以是两句不同的话'
        标签=态.get('searchLabels') if isinstance(态.get('searchLabels'),dict) else None
        if not isinstance(标签,dict):
            return 自身._翻译('status.empty')
        选项=态.get('options') if isinstance(态.get('options'),list) else []
        if len(选项)==0 and isinstance(标签.get('empty'),str):
            return 标签['empty']
        if isinstance(标签.get('noResults'),str):
            return 标签['noResults']
        return 自身._翻译('status.empty')

    def _改搜索(自身,弹出,事件):
        '按标签和说明过滤；相同文本不重画'
        下一=事件.value if hasattr(事件,'value') and isinstance(事件.value,str) else ''
        弹出.setSearch(下一)

    def _按键(自身,弹出,事件):
        '上下移动高亮，回车和 Tab 选中，Esc 和 Shift+Tab 关闭'
        键,移位=_键名(事件)
        态=弹出.state.getSnapshot()
        if not isinstance(态,dict) or 态.get('open') is not True:
            return
        行表=过滤选项(态.get('options'),态.get('search'),态.get('searchMode'))
        if 键=='ArrowDown':
            弹出.move(1)
            return
        if 键=='ArrowUp':
            弹出.move(-1)
            return
        if 键=='Enter':
            弹出.select(态.get('active') if isinstance(态.get('active'),int) else 0)
            return
        if 键=='Escape':
            弹出.dismiss({'focusComposer':True})
            return
        if 键!='Tab':
            return
        if 移位 is not True and (态.get('status')!='ready' or len(行表)==0):
            return
        if 移位:
            弹出.dismiss({'focusComposer':True})
            return
        弹出.select(态.get('active') if isinstance(态.get('active'),int) else 0)

    def _填状态(自身,弹出,态):
        '错误、加载中、应用中和空列表'
        if 自身.状态区 is None:
            return
        try:
            自身.状态区.clear()
        except Exception as 错:
            自身._模式=None
            界面.label(页面失败文案(错))
            return
        行表=过滤选项(态.get('options'),态.get('search'),态.get('searchMode'))
        with 自身.状态区:
            错误=态.get('error')
            if isinstance(错误,str) and 错误!='':
                with 界面.row().classes('dsh-cmd-error'):
                    界面.label(错误).classes('dsh-cmd-error-text')
                    if 态.get('status')=='failed':
                        界面.button(自身._翻译('retry'), on_click=弹出.retry).props('flat no-caps').classes('dsh-cmd-retry')
            if 态.get('status')=='pending':
                界面.label(自身._翻译('status.loading')).classes('dsh-cmd-status')
            if 态.get('submitting') is True:
                界面.label(自身._翻译('status.applying')).classes('dsh-cmd-status')
            if 态.get('status')=='ready' and len(行表)==0:
                界面.label(自身._空文(态)).classes('dsh-cmd-status')

    def _填列表(自身,弹出,态):
        '按过滤顺序画分组和行'
        if 自身.列表区 is None or 态.get('status')!='ready':
            if 自身.列表区 is not None:
                try:
                    自身.列表区.clear()
                except Exception as 错:
                    界面.label(页面失败文案(错))
            return
        try:
            自身.列表区.clear()
        except Exception as 错:
            自身._模式=None
            界面.label(页面失败文案(错))
            return
        行表=过滤选项(态.get('options'),态.get('search'),态.get('searchMode'))
        组表=分组选项(行表)
        高亮=态.get('active') if isinstance(态.get('active'),int) else 0
        序号=0
        with 自身.列表区:
            for 组 in 组表:
                组对象=组['group']
                if isinstance(组对象,dict):
                    标=组对象.get('label') if isinstance(组对象.get('label'),str) and 组对象['label']!='' else 组对象.get('name')
                    if isinstance(标,str) and 标!='':
                        界面.label(标).classes('dsh-cmd-group')
                for 选项 in 组['rows']:
                    _画行(弹出,选项,序号,序号==高亮)
                    序号+=1

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
            自身._已订=None
            自身._模式=None
        return 自身.渲染()

def _画行(弹出,选项,序号,当前):
    '一行：标签、徽标、说明、当前标记'
    行=界面.element('div').classes('dsh-cmd-row')
    if 当前:
        行.classes(add='dsh-cmd-row-active')
    行.props('role=option aria-selected='+('true' if 当前 else 'false'))
    def 点(_事件=None,下标=序号):
        '选中这一行'
        弹出.select(下标)
    def 停(_事件=None,下标=序号):
        '悬停移动高亮'
        弹出.highlight(下标)
    行.on('click',点)
    行.on('mouseenter',停)
    标=选项.get('label') if isinstance(选项.get('label'),str) else ''
    详=选项.get('detail') if isinstance(选项.get('detail'),str) else ''
    徽=选项.get('badge') if isinstance(选项.get('badge'),str) else ''
    with 行:
        with 界面.row().classes('dsh-cmd-label'):
            界面.label(标 if 标!='' else ' ').classes('dsh-cmd-label-text')
            if 徽!='':
                界面.label(徽).classes('dsh-cmd-badge')
        if 详!='':
            界面.label(详).classes('dsh-cmd-detail')
        if 选项.get('active') is True:
            界面.icon('check').classes('dsh-cmd-check')
