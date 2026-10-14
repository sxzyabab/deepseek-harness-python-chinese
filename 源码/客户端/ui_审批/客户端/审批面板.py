from nicegui import ui as 界面
from ...ui_基础界面组件.状态点 import 状态点
from ..异常 import 审批错误,页面失败文案#本包异常

样式表='''#对齐 ApprovalPanel.module.css，类名加前缀，避免盖到别的卡片
.approval-root{display:flex;flex-direction:column;align-items:center;padding:8px calc(var(--dsh-composer-side-clearance) + 16px) 12px}
.approval-card{overflow:hidden;width:100%;max-width:var(--dsh-chat-content-width);border:1px solid var(--dsw-alias-state-warn-secondary);border-radius:var(--dsw-radius-xl);background:var(--dsw-specific-input-major);box-shadow:var(--dsw-shadow-lv2);--dsh-scrollbar-thumb:var(--dsw-alias-scrollbar-bg-l2);--dsh-scrollbar-thumb-hover:var(--dsw-alias-scrollbar-hover-l2)}
.approval-strip{display:flex;align-items:center;gap:8px;padding:10px 16px;background:var(--dsw-alias-state-warn-tertiary);color:var(--dsw-alias-state-warn-primary);font-size:13px;line-height:18px}
.approval-body{display:flex;flex-direction:column;gap:6px;box-sizing:border-box;max-height:var(--dsh-composer-text-max-height);overflow-y:auto;padding:12px 16px 0}
.approval-headline{color:var(--dsw-alias-label-primary);font-size:15px;font-weight:500;line-height:24px}
.approval-command{color:var(--dsw-alias-label-tertiary);font-family:var(--ds-font-family-code);font-size:13px;line-height:20px;word-break:break-all}
.approval-actions{display:flex;justify-content:flex-end;gap:8px;padding:14px 16px}
.approval-reject:hover:not(:disabled){background:var(--dsw-alias-interactive-bg-hover-danger);color:var(--dsw-alias-state-error-primary);border-color:transparent}
'''#样式表结束
界面.add_css(样式表,shared=True)

def 腾出根(自身):
    '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句。'
    旧=getattr(自身,'根',None)
    if 旧 is None:
        return None
    try:
        旧.clear()
    except Exception as 错误:
        自身.根=None
        return 页面失败文案(错误)
    return None

def 标出失败(文案):
    '失败句非空时写在当前页面上'
    if isinstance(文案,str) and 文案!='':
        界面.label(文案)

__all__=['审批面板','审批流']#仅中文公开名

def 缺省翻译(键,_插值=None):
    '无翻译函数时回传键'
    return 键#键即文案

class 审批流:#一次性作答流
    '等待条+理由+详情槽+准/拒。父面板调用渲染，构造时不画'
    def __init__(自身,待处理,翻译,渲染槽=None):
        '记下待处理面、翻译与详情槽。详情槽在键齐时自己画，这里不再调用渲染'
        自身.pending=待处理#待处理面
        自身.t=翻译#翻译函数
        自身.渲染槽=渲染槽#conversation.approval.detail
        自身.已答=False#作答门闩
        自身.作答失败=None#上次作答失败句

    def 作答(自身,结果):
        '先禁用按钮；失败则恢复可点，并把失败句留在卡片上'
        自身.已答=True#先禁用
        自身.作答失败=None
        try:
            自身.pending.answer(结果)#作答
        except 审批错误 as 错误:
            自身.已答=False#恢复可点
            自身.作答失败=页面失败文案(错误)
        自身.渲染()#按钮态写在卡片上

    def 渲染(自身):
        '画出审批卡片。父面板会调用，构造时不画'
        翻译=自身.t#文案
        理由=自身.pending.reason#理由
        if 理由 is None:
            理由=翻译('escalation',{'toolName':自身.pending.toolName})#回退
        清除失败=腾出根(自身)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('approval-root')
        with 自身.根:
            标出失败(清除失败)
            标出失败(自身.作答失败)
            with 界面.column().classes('approval-card'):
                with 界面.row().classes('approval-strip'):
                    状态点({'state':'ongoing' if 自身.已答 else 'warning','appearance':'dot'}).渲染()
                    界面.label(翻译('waiting'))
                with 界面.column().classes('approval-body'):
                    界面.label(理由).classes('approval-headline')
                    调用=自身.pending.callId if 自身.pending is not None else None
                    if 调用 is not None and 自身.渲染槽 is not None:
                        with 界面.column().classes('approval-command'):
                            自身.渲染槽('conversation.approval.detail',{'callId':调用})
                with 界面.row().classes('approval-actions'):
                    拒=界面.button(翻译('reject'), on_click=自身.点拒绝).classes('approval-reject')
                    准=界面.button(翻译('allowOnce'), on_click=自身.点准一次)
                    if 自身.已答:
                        拒.disable()
                        准.disable()

    def 点拒绝(自身):
        '拒绝'
        自身.作答('rejected')#拒

    def 点准一次(自身):
        '仅本次允许'
        自身.作答('allowed-once')#准

class 审批面板:#链条目入口
    '渲染一个待处理审批及其可选的 Tool 自有详情'
    def __init__(自身,属性=None):
        '记下 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成
        自身._流=None#当前流
        自身._流键=None#流身份
        if 'matched' in 自身.属性 and 't' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换 key 则重建流'
        自身.属性=属性 if isinstance(属性,dict) else {}#新

    def 渲染(自身):
        '按 key 重挂载流'
        属性=自身.属性#props
        审批=属性['matched'] if 'matched' in 属性 else None#命中的待处理面
        清除失败=腾出根(自身)
        if 审批 is None:
            标出失败(清除失败)
            return None#空
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('approval-host')
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else None#子槽渲染
        翻译=属性['t'] if 't' in 属性 else 缺省翻译#文案
        if 自身._流 is None or 自身._流键!=审批.key:
            自身._流=审批流(审批,翻译,渲染槽)#新流，构造时不画
            自身._流键=审批.key
        else:
            自身._流.t=翻译#翻译
            自身._流.pending=审批#面
            自身._流.渲染槽=渲染槽#详情槽
            自身._流.根=None#父列已清空，卡片要新建
        with 自身.根:
            标出失败(清除失败)
            自身._流.渲染()

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
