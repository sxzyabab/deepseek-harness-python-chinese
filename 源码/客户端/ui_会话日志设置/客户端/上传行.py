'通用设置里的上传行，以及关掉设置后仍在的提示'

from nicegui import ui as 界面
from ...ui_基础界面组件.吐司 import 吐司

样式表='''
.上传行{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:16px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2);width:100%}
.上传标题{font-size:14px;line-height:20px}
.上传说明{margin-top:4px;color:var(--dsw-alias-label-secondary);font-size:12px;line-height:18px}
'''
界面.add_css(样式表,shared=True)

__all__=['上传行','上传提示']

_槽位键=('useUpload','useMutation','setEnabled')

class 上传行:
    '画出已接受的 API 上传状态'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if all(键 in 自身.属性 for 键 in _槽位键) and 't' in 自身.属性:
            自身.渲染()

    def 快照(自身):
        '选中只认 enabled 为真；忙、未就绪或不可写时禁用'
        上传=自身.属性['useUpload'](lambda 值:值)
        忙=自身.属性['useMutation'](lambda 值:值['busy'])
        return {
            '标题':自身.属性['t']('title'),
            '说明':自身.属性['t']('description'),
            '选中':(上传.get('value') or {}).get('enabled') is True if isinstance(上传,dict) else False,
            '禁用':忙 or (上传.get('status') if isinstance(上传,dict) else None)!='ready' or not (上传.get('writable') if isinstance(上传,dict) else False),
        }

    def 切换(自身,启用):
        自身.属性['setEnabled'](启用)

    def 渲染(自身):
        '缺 useUpload、useMutation、setEnabled 任一键时仍画标题和禁用开关，并写明缺的键名'
        属性=自身.属性 if isinstance(自身.属性,dict) else {}
        缺=[键 for 键 in _槽位键 if 键 not in 属性]
        if 缺:
            有文案='t' in 属性 and callable(属性['t'])
            标题=属性['t']('title') if 有文案 else ''
            with 界面.row().classes('上传行'):
                with 界面.column().style('gap:0'):
                    界面.label(标题).classes('上传标题')
                    if 有文案:
                        界面.label(属性['t']('description')).classes('上传说明')
                    界面.label('缺少 '+'、'.join(缺)).classes('上传说明')
                开关=界面.switch(value=False).props('aria-label="'+标题+'"')
                开关.disable()
            return
        态=自身.快照()
        with 界面.row().classes('上传行'):
            with 界面.column().style('gap:0'):
                界面.label(态['标题']).classes('上传标题')
                界面.label(态['说明']).classes('上传说明')
            def 改(事件):
                自身.切换(bool(事件.value))
            开关=界面.switch(value=态['选中'], on_change=改).props('aria-label="'+态['标题']+'"')
            if 态['禁用']:
                开关.disable()

    def __call__(自身,属性=None):
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

class 上传提示:
    '设置关掉后仍显示保存结果'
    def __init__(自身,属性):
        '记下 props。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 't' in 自身.属性 and 'useMutation' in 自身.属性 and 'dismiss' in 自身.属性:
            自身.渲染()

    def 快照(自身):
        状态=自身.属性['useMutation'](lambda 值:值)
        if 状态['notice'] is None:
            return None
        结果={
            '文本':自身.属性['t'](状态['notice']),
            '序号':状态['sequence'],
            '关掉':自身.属性['dismiss'],
        }
        if 状态['notice']=='saved':
            结果['语气']='success'
        return 结果

    def 渲染(自身):
        态=自身.快照()
        if 态 is None:
            return
        道具={'text':态['文本'],'onDone':态['关掉']}
        if 态.get('语气')=='success':
            道具['tone']='success'
        吐司(道具).渲染()

    def __call__(自身,属性=None):
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()
