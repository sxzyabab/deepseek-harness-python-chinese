import json
from nicegui import ui as 界面
from ..ui_基础界面组件.icons import 图标下chevron14,图标技能16,图标检视12
from .异常 import 技能错误,页面失败文案#本包异常

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

__all__=['技能错误','技能行','技能行模型','技能名','结果文本','首行','样式表']

样式表='''
.card{display:flex;flex-direction:column}
.row{position:relative;overflow:hidden;display:flex;align-items:center;height:24px;min-width:0}
.row[data-expandable]{cursor:pointer}
.card[data-state=running] .row::after{content:'';position:absolute;inset:0 auto 0 0;width:300px;background:linear-gradient(90deg,transparent 0%,color-mix(in srgb,var(--dsw-alias-bg-base) 60%,transparent) 55%,transparent 100%);animation:dsh-skill-row-sweep 2.6s ease-out infinite;pointer-events:none}
@keyframes dsh-skill-row-sweep{0%{left:-300px}90%,100%{left:100%}}
.leading{position:relative;flex:none;width:16px;height:16px;display:inline-flex;align-items:center;justify-content:center;margin-right:6px;color:var(--dsw-alias-label-tertiary)}
.chevron{color:var(--dsw-alias-label-secondary)}
.iconIdle{display:inline-flex;opacity:1;transition:opacity 100ms ease}
.chevronHover{position:absolute;inset:0;margin:auto;opacity:0;transition:opacity 100ms ease}
.row:hover .iconIdle{opacity:0}
.row:hover .chevronHover{opacity:1}
.title{flex:none;font-size:14px;line-height:24px;color:var(--dsw-alias-label-secondary)}
.separator{flex:none;width:2px;height:2px;border-radius:1px;margin:0 8px;background:var(--dsw-alias-label-caption)}
.summary{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;line-height:24px;color:var(--dsw-alias-label-tertiary)}
.errorSummary{color:var(--dsw-alias-state-error-primary)}
.stoppedSummary{color:var(--dsw-alias-state-warn-label)}
.bodyWrap{display:flex;flex-direction:column}
.instructionsCard{display:flex;flex-direction:column;max-height:260px;margin:4px 0 4px 4px;overflow:hidden;border:1px solid var(--dsw-alias-border-l1);border-radius:12px;background:var(--dsw-alias-markdown-code-block)}
.instructionsHeader{flex:none;padding:8px 12px;border-bottom:1px solid var(--dsw-alias-border-l2);background:var(--dsw-alias-markdown-code-block-banner);font-size:11px;font-weight:500;line-height:16px;color:var(--dsw-alias-label-caption);text-transform:uppercase;letter-spacing:0.04em}
.instructions{min-height:0;margin:0;padding:10px 12px 12px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:var(--dsw-font-markdown-code-block-small);color:var(--dsw-alias-label-secondary)}
.instructions[data-error]{color:var(--dsw-alias-state-error-primary)}
.inspectButton{display:inline-flex;align-self:flex-start;align-items:center;gap:4px;margin:4px 0 2px 4px;padding:2px 8px;border:1px solid var(--dsw-alias-border-l2);border-radius:999px;background:var(--dsw-alias-bg-base);color:var(--dsw-alias-label-secondary);font-size:11px;line-height:16px;cursor:pointer;opacity:0;transition:opacity 100ms ease}
.card:hover .inspectButton,.inspectButton:focus-visible{opacity:1}
.inspectButton:hover{background:var(--dsw-alias-interactive-bg-hover-solid);color:var(--dsw-alias-label-primary)}
.visuallyHidden{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (prefers-reduced-motion:reduce){.card[data-state=running] .row::after{animation:none;display:none}.iconIdle,.chevronHover,.inspectButton{transition:none}}
'''
界面.add_css(样式表,shared=True)

def 首行(文本):
    '折叠错误摘要与畸形参数回退用的第一物理行'
    换行=文本.find('\n')
    if 换行==-1:
        return 文本
    return 文本[:换行]

def 技能名(原始参数,调用标识):
    '紧凑行唯一呈现的调用参数是技能名'
    try:
        解析=json.loads(原始参数)
        if isinstance(解析,dict) and 解析 is not None:
            名=解析['name'] if 'name' in 解析 else None
            if isinstance(名,str) and 名!='':
                return 首行(名)
    except (TypeError,ValueError,json.JSONDecodeError):
        pass
    if 原始参数=='':
        return 调用标识
    return 首行(原始参数)

def 结果文本(块):
    '压平耐久结果块；与 ui-tool 的 resultText 合同一致'
    if not isinstance(块,dict) or 'kind' not in 块:
        return None
    内容=块['content'] if 'content' in 块 and 块['content'] is not None else []
    错误=块['error'] if 'error' in 块 else None
    片段=[]
    for 项 in 内容:
        if isinstance(项,dict) and 'type' in 项 and 项['type']=='text':
            片段.append(项['text'] if 'text' in 项 and 项['text'] is not None else '')
        else:
            片段.append(json.dumps(项,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2))
    if len(片段)==0 and 错误 is not None:
        错名=错误['name'] if isinstance(错误,dict) and 'name' in 错误 else None
        错码=错误['code'] if isinstance(错误,dict) and 'code' in 错误 else None
        片段.append(str(错名)+': '+str(错码))
    接合='\n'.join(片段)
    if 接合=='':
        return None
    return 接合

def 技能行模型(块):
    '只从耐久 call 切片派生展示状态，不查活技能目录'
    已结算=isinstance(块,dict) and 'kind' in 块
    调用=块['call'] if 已结算 and 'call' in 块 else None
    原文=((调用['argsRaw'] if 调用 is not None and 'argsRaw' in 调用 else None) if 已结算 else (块['argsRaw'] if 'argsRaw' in 块 else None))
    原始参数='' if 原文 is None else 原文
    调用标识=块['callId'] if 'callId' in 块 and 块['callId'] is not None else ''
    错误=块['error'] if 'error' in 块 else None
    是错=块['isError'] if 'isError' in 块 else False
    if not 已结算:
        状态='running'
    elif isinstance(错误,dict) and 'code' in 错误 and 错误['code']=='interrupted':
        状态='stopped'
    elif 是错:
        状态='error'
    else:
        状态='ok'
    输出=结果文本(块)
    return {
        'name':技能名(原始参数,调用标识),
        'output':输出,
        'errorSummary':首行(输出) if 状态=='error' and 输出 is not None else None,
        'state':状态,
    }

class 已开始技能行:
    '已开始的技能行。父组件先空构造，再更新并渲染'
    def __init__(自身):#空构造
        '折叠状态留在这一份上'
        自身.属性={}#props
        自身.已展开=False#折叠
        自身.重画=None#父组件重画

    def 更新(自身,属性,重画):#刷新
        '记下 props 与重画'
        自身.属性=属性#props
        自身.重画=重画#重画

    def 切换展开(自身):#折叠
        '开则关，关则开'
        自身.已展开=not 自身.已展开#翻转

    def 渲染(自身):#画出已开始的行
        '标题、摘要、展开后的说明与检视'
        块=自身.属性['block'] if 'block' in 自身.属性 else None#调用块
        if not isinstance(块,dict):#没有块
            return#不画
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else None#文案
        检查=自身.属性['inspect'] if 'inspect' in 自身.属性 else None#检视
        模型=技能行模型(块)#模型
        可展开=模型['output'] is not None
        打开=自身.已展开 is True and 可展开 is True#当前展开
        if 模型['state']=='running' and 翻译 is not None:#进行中
            状态文案=翻译('row.running')#隐藏文案
        elif 模型['state']=='error' and 翻译 is not None:#失败
            状态文案=翻译('row.failed')#隐藏文案
        else:#成功或中止不另写状态
            状态文案=None#无
        if 模型['state']=='stopped' and 翻译 is not None:#中止写在摘要上
            摘要=翻译('row.stopped')#中止
        elif 模型['errorSummary'] is not None:#错误摘要
            摘要=模型['errorSummary']#第一行
        else:#技能名
            摘要=模型['name']#名字
        摘要类='summary'#摘要类
        if 模型['state']=='error':#失败色
            摘要类=摘要类+' errorSummary'#错误
        elif 模型['state']=='stopped':#中止色
            摘要类=摘要类+' stoppedSummary'#中止
        def 点展开():#点击行
            '有输出才切换'
            if 可展开 is not True:#不可展开
                return
            自身.切换展开()#翻转
            if callable(自身.重画):
                自身.重画()#重画
        def 按键(事件):#键盘
            'Enter 或空格等同点击'
            if 可展开 is not True:#不可展开
                return
            参数=事件.args if hasattr(事件,'args') else None#事件参数
            键=参数['key'] if isinstance(参数,dict) and 'key' in 参数 else None#键
            if 键 not in ('Enter',' '):#不是确认键
                return
            点展开()#切换
        卡=界面.element('div').classes('card')#卡
        卡.props('data-tool=skill data-state='+模型['state'])#状态
        with 卡:#内容
            行盒=界面.element('div').classes('row')#行
            if 可展开 is True:#可点
                行盒.props('data-expandable role=button tabindex=0')#按钮
                行盒.props('aria-expanded='+('true' if 打开 is True else 'false'))#展开
                行盒.on('click',点展开)#点击
                行盒.on('keydown',按键)#键盘
            with 行盒:#行内容
                with 界面.element('span').classes('leading'):#前导
                    if 打开 is True:#已展开
                        图标下chevron14({'className':'chevron','size':14})#箭头
                    elif 可展开 is not True:#不能展开
                        图标技能16({'size':14})#技能
                    else:#悬停换成箭头
                        with 界面.element('span').classes('iconIdle'):#静止图标
                            图标技能16({'size':14})#技能
                        图标下chevron14({'className':'chevron chevronHover','size':14})#箭头
                if isinstance(状态文案,str) and 状态文案!='':#隐藏状态
                    界面.label(状态文案).classes('visuallyHidden')#读屏
                if 翻译 is not None:
                    界面.label(翻译('row.title')).classes('title')#标题
                界面.element('span').classes('separator')#分隔点
                if isinstance(摘要,str):#摘要
                    界面.label(摘要).classes(摘要类)#摘要
            if 打开 is True:#展开体
                with 界面.element('div').classes('bodyWrap'):#体
                    区=界面.element('section').classes('instructionsCard')#说明卡
                    if 翻译 is not None:
                        区.props('aria-label="'+翻译('row.instructions').replace('"','')+'"')#无障碍
                    with 区:#说明
                        if 翻译 is not None:#页眉
                            界面.label(翻译('row.instructions')).classes('instructionsHeader')#页眉
                        输出=模型['output']#输出
                        说明=界面.label('' if 输出 is None else 输出).classes('instructions')#正文
                        if 模型['state']=='error':#失败色
                            说明.props('data-error')#标记
                    if callable(检查):
                        def 点检视():#打开检视
                            '调用注入的检视'
                            检查()#调用
                        检视=界面.element('button').classes('inspectButton').props('type=button')#按钮
                        检视.on('click',点检视)#点击
                        with 检视:#内容
                            图标检视12()#图标
                            if 翻译 is not None:#文案
                                界面.label(翻译('row.inspect'))#查看

class 技能行:
    '渲染一条 skill 工具调用为强调摘要与说明披露'
    def __init__(自身,属性=None):#槽位构造
        '槽位只调用构造，键齐了就画'
        自身.属性={} if 属性 is None else 属性#props
        自身.已开始=已开始技能行()#空构造，不画
        if isinstance(自身.属性,dict) and ('block' in 自身.属性 or 'phase' in 自身.属性):
            自身.渲染()

    def 更新(自身,属性):#刷新
        '刷新合成 props'
        自身.属性=属性#新

    def 渲染(自身):#画出技能行
        '准备中只画标题；已开始的行交给子组件'
        清除失败=腾出根(自身)
        if getattr(自身,'根',None) is None:#尚无根
            自身.根=界面.column().classes('skill-row')#根
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else None#文案
        阶段=自身.属性['phase'] if 'phase' in 自身.属性 else None#阶段
        with 自身.根:#内容
            标出失败(清除失败)
            if 阶段=='preparing':#准备中
                卡=界面.element('div').classes('card')#卡
                卡.props('data-tool=skill data-state=preparing')#准备
                with 卡:#行
                    with 界面.element('div').classes('row'):#行
                        with 界面.element('span').classes('leading'):#图标
                            图标技能16({'size':14})#技能
                        if 翻译 is not None:#文案
                            界面.label(翻译('row.preparing')).classes('visuallyHidden')#读屏
                            界面.label(翻译('row.title')).classes('title')#标题
                return#准备中没有说明
            自身.已开始.更新(自身.属性,自身.渲染)#刷新子组件
            自身.已开始.渲染()#由父组件画

    def __call__(自身,属性=None):#组件调用形
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
