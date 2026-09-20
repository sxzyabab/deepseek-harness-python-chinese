import json

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

class 技能错误(Exception):
    """本包异常基类。"""
    def __init__(自身,消息):
        """记下消息。"""
        super().__init__(消息)

def 首行(文本):
    """折叠错误摘要与畸形参数回退用的第一物理行。"""
    换行=文本.find('\n')
    if 换行==-1:
        return 文本
    return 文本[:换行]

def 技能名(原始参数,调用标识):
    """紧凑行唯一呈现的调用参数是技能名。"""
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
    """压平耐久结果块；与 ui-tool 的 resultText 合同一致。"""
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
    """只从耐久 call 切片派生展示状态，不查活技能目录。"""
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

class 技能行:
    """渲染一条 skill 工具调用为强调摘要与说明披露。"""
    def __init__(自身,属性=None):
        """记下 props 与折叠状态。"""
        自身.属性={} if 属性 is None else 属性
        自身.已展开=False

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性

    def 切换展开(自身):
        """切换展开状态。"""
        自身.已展开=not 自身.已展开

    def 渲染(自身):
        """产出结构化视图描述。"""
        块=自身.属性['block'] if 'block' in 自身.属性 else None
        翻译=自身.属性['t'] if 't' in 自身.属性 else None
        检查=自身.属性['inspect'] if 'inspect' in 自身.属性 else None
        模型=技能行模型(块)
        可展开=模型['output'] is not None
        打开=自身.已展开 and 可展开
        if 模型['state']=='running':
            状态文案=翻译('row.running') if 翻译 else None
        elif 模型['state']=='error':
            状态文案=翻译('row.failed') if 翻译 else None
        elif 模型['state']=='stopped':
            状态文案=翻译('row.stopped') if 翻译 else None
        else:
            状态文案=None
        摘要=模型['errorSummary'] if 模型['errorSummary'] is not None else 模型['name']
        return {
            'type':'skill-row',
            'state':模型['state'],
            'expandable':可展开,
            'open':打开,
            'status':状态文案,
            'summary':摘要,
            'output':模型['output'] if 打开 else None,
            'instructionsLabel':翻译('row.instructions') if 翻译 and 打开 else None,
            'inspect':检查 if 打开 else None,
            'toggle':自身.切换展开,
        }

    def __call__(自身,属性=None):
        """有新属性则刷新后渲染。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
