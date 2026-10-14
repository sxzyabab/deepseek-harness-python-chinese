from nicegui import ui as 界面
from ...客户端.存储 import 创建快照存储#快照存储
from .异常 import 页面失败文案

样式表='''#对齐 FeedbackDialog.module.css，类名加前缀，避免盖到别的对话框
.feedback-card{gap:38px;width:min(488px,100%);border-radius:var(--dsw-radius-panel)}
.feedback-categories{display:flex;flex-wrap:wrap;gap:8px;margin-top:-14px}
.feedback-chip{height:28px;padding:0 12px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-sm);background:transparent;color:var(--dsw-alias-label-primary);font:inherit;font-size:13px;line-height:18px;cursor:pointer;transition:background-color 120ms ease,border-color 120ms ease,color 120ms ease}
.feedback-chip:hover:not(:disabled){background:var(--dsw-alias-interactive-bg-hover);color:var(--dsw-alias-label-primary)}
.feedback-chip:disabled{cursor:default;opacity:0.4}
.feedback-chip:focus-visible{outline:var(--dsw-focus-ring-width) solid var(--dsw-focus-ring-color,var(--dsw-alias-state-business-primary));outline-offset:2px}
.feedback-chip-on,.feedback-chip-on:hover:not(:disabled){border-color:var(--dsw-alias-button-primary-fill);background:var(--dsw-alias-button-primary-fill);color:var(--dsw-alias-label-primary-foreground)}
.feedback-detail{display:block;width:100%;min-height:116px;max-height:280px;box-sizing:border-box;margin-top:18px;padding:12px 14px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-lg);background:var(--dsw-alias-bg-layer-1);color:var(--dsw-alias-label-primary);font:inherit;font-size:14px;line-height:22px;field-sizing:content;resize:none;transition:border-color 120ms ease,box-shadow 120ms ease}
.feedback-detail::placeholder{color:var(--dsw-alias-label-caption)}
.feedback-detail:focus{outline:none;border-color:var(--dsw-alias-border-l3);box-shadow:0 0 0 1px var(--dsw-alias-state-business-primary)}
.feedback-submit{width:100%;height:44px;border-radius:var(--dsw-radius-lg);font-size:14px;font-weight:500}
@media (prefers-reduced-motion:reduce){.feedback-chip,.feedback-detail{transition:none}}
'''#样式表结束
界面.add_css(样式表,shared=True)

__all__=['反馈对话框控制器','反馈对话框','关闭草稿','反馈类别']#仅中文公开名

反馈类别=(#对话框芯片顺序
    'task-result','instruction-following','product-interaction','service-stability',
    'resource-cost','security-privacy-permission','other',
)#类别结束

失败文案键={#失败码 → 文案键
    'version-conflict':'error.conflict',
    'note-too-large':'error.noteTooLarge',
}#失败键结束

关闭草稿={'target':None,'category':None,'text':'','submitting':False,'failure':None}#关闭草稿（无 toast）

class 反馈对话框控制器:#按会话对话框控制器
    '一份实例支撑覆盖层入口与每个消息控件'
    def __init__(自身,提交):
        '提交接收 (目标, 条目) 并返回动作结果 dict'
        自身._提交=提交#提交函数
        初始=dict(关闭草稿)#拷贝
        初始['toast']=0#无轻提示
        自身.状态=创建快照存储(初始)#状态存储
        自身._代数=0#代数
        自身._轻提示序号=0#轻提示序号

    def 打开(自身,目标):#打开
        '以空草稿打开，替换任何已打开草稿'
        自身._代数+=1#换代
        下一=dict(关闭草稿)#空草稿
        下一['target']=目标#目标
        下一['toast']=自身.状态.getSnapshot()['toast']#保留 toast
        自身.状态.set(下一)#发布

    def 关闭(自身):#关闭
        '关闭对话框并丢弃草稿；屏幕上的轻提示保留'
        自身._代数+=1#换代
        下一=dict(关闭草稿)#空草稿
        下一['toast']=自身.状态.getSnapshot()['toast']#保留 toast
        自身.状态.set(下一)#发布

    def 编辑(自身,草稿):#编辑
        '在可编辑时替换草稿的一部分。草稿为 dict'
        当前=自身.状态.getSnapshot()#当前
        if 当前['target'] is None or 当前['submitting']:#关闭或提交中
            return#忽略
        下一=dict(当前)#拷贝
        下一.update(草稿)#合并
        自身.状态.set(下一)#发布

    def 提交草稿(自身):#提交草稿
        '提交草稿；空草稿也合法。成功关闭并拉起轻提示'
        当前=自身.状态.getSnapshot()#当前
        if 当前['target'] is None or 当前['submitting']:#关闭或提交中
            return#忽略
        代数=自身._代数#记下代数
        下一=dict(当前)#拷贝
        下一['submitting']=True#提交中
        下一['failure']=None#清失败
        自身.状态.set(下一)#发布
        正文=当前['text'].strip()#规范化
        条目={}#记录
        if len(正文)>0:#有正文
            条目['text']=正文#正文
        if 当前['category'] is not None:#有类别
            条目['category']=当前['category']#类别
        结果=自身._提交(当前['target'],条目)#提交
        if 'ok' in 结果 and 结果['ok']:#成功
            if 代数==自身._代数:#同代才关闭
                自身.关闭()#关闭
            自身.确认()#轻提示
            return
        if 代数!=自身._代数:#草稿已换代
            return#遗弃
        现=dict(自身.状态.getSnapshot())#现状态
        现['submitting']=False#结束提交
        错误=结果['error'] if 'error' in 结果 else {}#错误
        现['failure']=错误['code'] if 'code' in 错误 else None#失败码
        现['toast']=0#清确认 toast
        自身.状态.set(现)#发布

    def 关掉失败(自身):#关掉失败提示
        '清掉当前失败轻提示，不关闭草稿'
        现=dict(自身.状态.getSnapshot())#现
        现['failure']=None#清失败
        自身.状态.set(现)#发布

    def 确认(自身):#确认轻提示
        '显示确认轻提示；已有则重启'
        自身._轻提示序号+=1#递增
        现=dict(自身.状态.getSnapshot())#现
        现['toast']=自身._轻提示序号#序号
        自身.状态.set(现)#发布

    def 退役轻提示(自身,序号):#退役轻提示
        '轻提示淡出后退役一份'
        现=自身.状态.getSnapshot()#现
        if 现['toast']==序号:#同序号
            下一=dict(现)#拷贝
            下一['toast']=0#清
            自身.状态.set(下一)#发布

    def 拆除(自身):#拆除
        '丢掉草稿与轻提示'
        自身._代数+=1#换代
        下一=dict(关闭草稿)#空
        下一['toast']=0#清 toast
        自身.状态.set(下一)#发布

def 对话框键齐(属性):
    '状态源和五个动词都在才画'
    if not isinstance(属性,dict):#不是合成 props
        return False#不齐
    for 键 in ('edit','submit','dismiss','dismissFailure','dismissToast'):#动词
        if 键 not in 属性 or not callable(属性[键]):#缺动词
            return False#不齐
    if 'useDialog' in 属性 and 属性['useDialog'] is not None:#选择器
        return True#齐
    钩=属性['hooks'] if 'hooks' in 属性 else None#钩子表
    if isinstance(钩,dict) and 'dialog' in 钩 and 钩['dialog'] is not None:#状态仓
        return True#齐
    return False#没有状态

class 反馈对话框:#会话反馈对话框
    '类别芯片、说明框、提交，以及确认与失败提示'
    def __init__(自身,属性):
        '记下 props 并画出对话框'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已订=False
        自身.改稿中=False
        自身.画面失败=None
        if 对话框键齐(自身.属性):#键齐
            自身.渲染()#构造末尾才画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 文(自身,键):
        '词表；缺座位时用键'
        译=自身.属性.get('t')
        if callable(译):
            return 译(键)
        return 键

    def 调用(自身,名,*参数):
        '缺动词则跳过'
        函=自身.属性.get(名)
        if callable(函):
            return 函(*参数)
        return None

    def 订状态(自身):
        '对话框状态变了就重画；改说明时不拆输入框'
        if 自身.已订:
            return
        自身.已订=True
        用=自身.属性.get('useDialog')
        订=getattr(用,'_subscribe',None) if 用 is not None else None
        if not callable(订):
            钩=自身.属性.get('hooks')
            源=钩.get('dialog') if isinstance(钩,dict) else (getattr(钩,'dialog',None) if 钩 is not None else None)
            订=getattr(源,'subscribe',None)
        if not callable(订):
            return
        def 重画():
            '状态变了再画'
            if 自身.改稿中:
                return
            根=getattr(自身,'根',None)
            if 根 is None:
                return
            槽=getattr(根,'parent_slot',None)
            if 槽 is not None and getattr(槽,'parent',None) is None:
                return
            自身.渲染()
        订(重画)

    def 读状态(自身):
        'hooks.dialog 或 useDialog'
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}
        存储=钩['dialog'] if 'dialog' in 钩 else None
        if 存储 is not None:
            return 存储.getSnapshot()
        用=自身.属性['useDialog'] if 'useDialog' in 自身.属性 else None
        if 用 is not None:
            return 用(lambda 快照:快照)
        return dict(关闭草稿)

    def 渲染(自身):
        '打开时画对话框；有轻提示或失败时画一句'
        翻译=自身.文
        状态=自身.读状态()
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:
                自身.根=None
                自身.画面失败=页面失败文案(错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('feedback-dialog')
        失败码=状态['failure'] if 'failure' in 状态 else None
        轻提示=状态['toast'] if 'toast' in 状态 else 0
        目标=状态['target'] if 'target' in 状态 else None
        提交中=状态['submitting'] is True if 'submitting' in 状态 else False
        类别=状态['category'] if 'category' in 状态 else None
        正文=状态['text'] if 'text' in 状态 and 状态['text'] is not None else ''
        with 自身.根:
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            if 失败码 is not None:
                键=失败文案键[失败码] if 失败码 in 失败文案键 else 'error.generic'
                界面.label(翻译(键))
                def 关失败():
                    '清失败提示'
                    自身.调用('dismissFailure')
                    自身.渲染()
                界面.button(翻译('close'),on_click=关失败).props('flat no-caps')
            elif isinstance(轻提示,int) and 轻提示>0:
                界面.label(翻译('toast.recorded'))
                def 关提示(序号=轻提示):
                    '退役这份轻提示'
                    自身.调用('dismissToast',序号)
                    自身.渲染()
                界面.button(翻译('close'),on_click=关提示).props('flat no-caps')
            if 目标 is not None:
                with 界面.dialog() as 对话框:
                    with 界面.card().classes('feedback-card'):
                        界面.label(翻译('dialog.title'))
                        界面.label(翻译('dialog.categories'))
                        with 界面.row().classes('feedback-categories'):
                            for 项 in 反馈类别:
                                def 点类(_事件=None,标识=项,当前=类别):
                                    '再点已选则取消'
                                    自身.调用('edit',{'category':None if 当前==标识 else 标识})
                                    自身.渲染()
                                芯片类='feedback-chip feedback-chip-on' if 类别==项 else 'feedback-chip'
                                芯片=界面.button(翻译('category.'+项),on_click=点类).props('flat no-caps').classes(芯片类)
                                if 类别==项:
                                    芯片.props('aria-pressed=true')
                                if 提交中:
                                    芯片.disable()
                        def 改文(事件):
                            '写入说明'
                            自身.改稿中=True
                            try:
                                自身.调用('edit',{'text':事件.value})
                            finally:
                                自身.改稿中=False
                        框=界面.textarea(翻译('dialog.detail'),value=正文,placeholder=翻译('dialog.hint'),on_change=改文).classes('feedback-detail')
                        if 提交中:
                            框.disable()
                        def 点提交():
                            '提交草稿'
                            自身.调用('submit')
                            自身.渲染()
                        def 点关():
                            '关掉对话框'
                            自身.调用('dismiss')
                            自身.渲染()
                        提交钮=界面.button(翻译('submitting' if 提交中 else 'submit'),on_click=点提交).classes('feedback-submit')
                        if 提交中:
                            提交钮.disable()
                        界面.button(翻译('close'),on_click=点关).props('flat no-caps')
                对话框.open()
        自身.订状态()

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
