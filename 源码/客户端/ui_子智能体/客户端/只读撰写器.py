from nicegui import ui as 界面

__all__=['只读撰写器','样式表']#仅中文公开名

样式表='''#对齐 SubagentReadOnlyComposer.module.css
.frame{display:flex;align-items:center;justify-content:center;gap:8px;margin:0 24px 20px;min-height:54px;padding:10px 16px;border:1px solid var(--dsw-alias-border-l2);border-radius:14px;background:var(--dsw-alias-bg-layer-1);color:var(--dsw-alias-label-tertiary);font-size:13px;line-height:20px}
.frame strong{color:var(--dsw-alias-label-primary);font-weight:510}
'''#样式表结束
界面.add_css(样式表,shared=True)

class 只读撰写器:#只读撰写器替换面
    '说明为何普通撰写器不可用'

    def __init__(自身,属性):#记下 props
        '记下匹配原因与翻译。槽位只调用构造，键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        if 'matched' in 自身.属性 and 't' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):#刷新 props
        '刷新合成 props'
        自身.属性=属性#新 props

    def 渲染(自身):#产出结构树
        '与上游 JSX 同构'
        if 'matched' not in 自身.属性 or 't' not in 自身.属性:#槽位还没齐
            return#不画
        匹配=自身.属性['matched']#认领结果
        翻译=自身.属性['t']#文案
        原因=匹配['reason'] if isinstance(匹配,dict) and 'reason' in 匹配 else ''#原因
        一次性=原因=='one-shot'#一次性
        标题键='readonly.oneShot.title' if 一次性 else 'readonly.title'#标题键
        if 原因=='unknown':#未知
            正文键='readonly.unknown.body'#未知正文
        elif 一次性:#一次性
            正文键='readonly.oneShot.body'#一次性正文
        else:#父会话不在线
            正文键='readonly.body'#续跑正文
        def 转义(文):
            '放进 HTML'
            return str(文).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        with 界面.row().classes('frame'):
            界面.html('<strong>'+转义(翻译(标题键))+'</strong>',sanitize=False)
            界面.label(翻译(正文键))

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
