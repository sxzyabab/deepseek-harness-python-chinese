"""技能工具行：按键 toolview 洞上的域拥有行。

对齐上游 `ui-skill/src/client/SkillRow.tsx`。公开面仅中文名。
紧凑强调行保持已加载说明在回放中可扫；精确耐久工具输出仍在有界披露卡中可用。
"""
import json#解析调用参数

__all__=['技能行','技能行模型','技能名','结果文本','首行','样式表']#仅中文公开名

样式表='''#对齐 SkillRow.module.css
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
'''#样式表结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 首行(文本):#取第一物理行
    """折叠错误摘要与畸形参数回退用的第一物理行。"""
    换行=文本.find('\n')#找换行
    if 换行==-1:#无换行
        return 文本#整段
    return 文本[:换行]#切到换行前

def 技能名(原始参数,调用标识):#从参数解析技能名
    """紧凑行唯一呈现的调用参数是技能名。"""
    try:#尝试解析 JSON
        解析=json.loads(原始参数)#解析
        if isinstance(解析,dict) and 解析 is not None:#对象
            名=解析.get('name')#name 字段
            if isinstance(名,str) and 名!='':#非空字符串
                return 首行(名)#第一行
    except Exception:#流式可能暴露截断 JSON 前缀
        pass#仍用原文第一行
    if 原始参数=='':#空参数
        return 调用标识#回退 callId
    return 首行(原始参数)#原文第一行

def 结果文本(块):#压平耐久结果块
    """压平耐久结果块；与 ui-tool 的 resultText 合同对齐。"""
    if 'kind' not in 块 and not hasattr(块,'kind'):#未结算块无 kind
        if isinstance(块,dict) and 'kind' not in 块:#映射无 kind
            return None#无结果
        if not isinstance(块,dict) and not hasattr(块,'kind'):#对象无 kind
            return None#无结果
    if isinstance(块,dict):#映射形态
        if 'kind' not in 块:#无 kind
            return None#无结果
        内容=块.get('content',[])#内容块
        错误=块.get('error')#错误
    else:#对象形态
        if not hasattr(块,'kind'):#无 kind
            return None#无结果
        内容=取字段(块,'content',[])#内容块
        错误=取字段(块,'error')#错误
    片段=[]#文本片段
    for 项 in 内容:#逐项
        if 取字段(项,'type')=='text':#文本块
            片段.append(取字段(项,'text',''))#文本
        else:#其它块
            片段.append(json.dumps(项,ensure_ascii=False,indent=2))#JSON
    if len(片段)==0 and 错误 is not None:#无正文但有错误
        片段.append(str(取字段(错误,'name'))+': '+str(取字段(错误,'code')))#错误摘要
    接合='\n'.join(片段)#拼接
    if 接合=='':#空
        return None#无结果
    return 接合#结果文本

def 技能行模型(块):#派生展示模型
    """只从耐久 call 切片派生展示状态，不查活技能目录。"""
    已结算=isinstance(块,dict) and 'kind' in 块 or (not isinstance(块,dict) and hasattr(块,'kind'))#是否已结算
    if isinstance(块,dict):#映射
        原始参数=(取字段(取字段(块,'call'),'argsRaw') if 已结算 else 块.get('argsRaw')) or ''#参数原文
        调用标识=块.get('callId','')#调用 id
        错误=块.get('error')#错误
        是错=块.get('isError',False)#是否错误
    else:#对象
        原始参数=(取字段(取字段(块,'call'),'argsRaw') if 已结算 else 取字段(块,'argsRaw')) or ''#参数原文
        调用标识=取字段(块,'callId','')#调用 id
        错误=取字段(块,'error')#错误
        是错=取字段(块,'isError',False)#是否错误
    if not 已结算:#进行中
        状态='running'#运行中
    elif 取字段(错误,'code')=='interrupted':#中止
        状态='stopped'#已中止
    elif 是错:#错误
        状态='error'#失败
    else:#成功
        状态='ok'#完成
    输出=结果文本(块)#结果文本
    return {#紧凑回放稳定视图模型
        'name':技能名(原始参数,调用标识),#技能名
        'output':输出,#输出
        'errorSummary':首行(输出) if 状态=='error' and 输出 is not None else None,#错误摘要
        'state':状态,#生命周期
    }#模型结束

class 技能行:#技能 toolview 组件
    """渲染一条 skill 工具调用为强调摘要与说明披露。"""
    def __init__(自身,属性=None):#可选初始 props
        """记下 props 与折叠状态。"""
        自身.属性=属性 or {}#合成 props
        自身.已展开=False#折叠状态

    def 更新(自身,属性):#刷新 props
        """刷新合成 props。"""
        自身.属性=属性#新 props

    def 切换展开(自身):#切换折叠
        """切换展开状态。"""
        自身.已展开=not 自身.已展开#翻转

    def 渲染(自身):#产出结构化视图
        """产出与上游 JSX 同构的结构化视图描述。"""
        块=取字段(自身.属性,'block')#工具块
        翻译=取字段(自身.属性,'t')#翻译座位
        检查=取字段(自身.属性,'inspect')#检查回调
        模型=技能行模型(块)#视图模型
        可展开=模型['output'] is not None#有输出才可展开
        打开=自身.已展开 and 可展开#实际打开
        if 模型['state']=='running':#运行中
            状态文案=翻译('row.running') if 翻译 else None#运行文案
        elif 模型['state']=='error':#失败
            状态文案=翻译('row.failed') if 翻译 else None#失败文案
        elif 模型['state']=='stopped':#中止
            状态文案=翻译('row.stopped') if 翻译 else None#中止文案
        else:#成功
            状态文案=None#无状态文案
        摘要=模型['errorSummary'] if 模型['errorSummary'] is not None else 模型['name']#摘要
        return {#结构化视图
            'type':'skill-row',#行类型
            'state':模型['state'],#生命周期
            'expandable':可展开,#可否展开
            'open':打开,#是否打开
            'status':状态文案,#无障碍状态文案
            'summary':摘要,#摘要
            'output':模型['output'] if 打开 else None,#打开时的说明
            'instructionsLabel':翻译('row.instructions') if 翻译 and 打开 else None,#说明标签
            'inspect':检查 if 打开 else None,#检查回调
            'toggle':自身.切换展开,#切换折叠
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
