"""fixture 展示样本常量、模型目录与工具视图/投影/检索辅助。

对齐上游 `connection/src/client/fixture.ts` 样本区与 present*/viewFor/投影/检索叶。
公开面仅中文名；协议键（type/card/kind 等）保持英文。
"""
import json,unicodedata#参数解析与码点分类
from .接口 import 会话搜索结果上限#检索条数上限

__all__=[#仅中文公开名
    '降sgr','markdown样本','用户markdown字面量','终端输出样本','终端退出状态',
    '搜索命中样本','搜索命中正文','搜索路径样本','搜索路径正文',
    '读样本首行','读样本源','读样本行','读样本路径','读样本总行','读样本正文',
    '网页搜索结果','网页抓取结果','夹具图像数据','夹具图像引用',
    '夹具模型分组','夹具用量','权限预设表',
    '取字符串','展示调用','展示结果','视图为','折计划','计划视图于',
    '权限选择于','用量样本于','令牌用量于','会话统计于',
    '估算夹具内容','上下文组成于','最近请求上下文','上下文压力于',
    '投影值于','投影帧于','分页于','日志引用附件','检索块文本','检索事件文本',
    '检索令牌跨度','短语匹配','检索摘录','比较检索候选','回扫待办','回扫目标',
    '折表面','派生事件消息','是否令牌增量','字符每令牌','块开销','角色开销',
]#公开面结束

def 降sgr(码,正文):#包 SGR
    """属性开 + 正文 + 复位。用 \\u001b 写转义，源文件里不出现字面控制字节。"""
    return f'\u001b[{码}m{正文}\u001b[0m'#开属性、正文、复位

markdown样本='\n'.join([#助手 Markdown 渲染样本（标题/强调/列表/表格/链接/代码块）
    '# Markdown fixture','',
    'Assistant output renders **strong text**, *emphasis*, and `inline code`.','',
    '- first item','  - nested item','',
    '| Area | State |','| --- | --- |','| history | rendered |','| streaming | stable |','',
    '[DeepSeek](https://www.deepseek.com)','','```ts','const markdown = true','```',
])#拼成单字符串
用户markdown字面量='用户字面量：# 不渲染 `code` [link](https://example.com)'#井号与反引号不得当 Markdown 渲染

#第 66 轮终端样本：覆盖第 60 轮两行 prompt 够不到的终端卡能力——
#basic-16 SGR 前景（绿/红/亮黑）、加粗、应对齐表格、超过 DEFAULT_TERMINAL_MAX_LINES（16）。
#退出状态另写在 终端退出状态；正文故意不含 `[exit code: N]`。
终端输出样本='\n'.join([#ANSI 终端输出样本
    降sgr(1,'Running 4 checks'),
    f"{降sgr(32,'\u2713')} typecheck                                          1.82s",
    f"{降sgr(32,'\u2713')} lint                                               0.94s",
    f"{降sgr(32,'\u2713')} duplication                                        2.10s",
    f"{降sgr(31,'\u2717')} unit                                               8.41s",
    '',
    降sgr(90,'packages/client/ui-primitives/tests/terminal-block.client.spec.tsx'),
    f"  {降sgr(31,'FAIL')} caps output at the configured line budget",
    '    expected 16 lines, received 24','',
    'NAME                        LINES    BRANCHES    FUNCTIONS    UNCOVERED',
    'TerminalBlock.tsx           100%     100%        100%         -',
    'ansi.ts                     100%     100%        100%         -',
    'clipboard.ts                100%     100%        100%         -',
    'CodeBlock.tsx               98.4%    96.2%       100%         41-43',
    'highlight.ts                100%     100%        100%         -',
    'Pill.tsx                    100%     100%        100%         -',
    'StateDot.tsx                100%     100%        100%         -',
    'markdown/Markdown.tsx       100%     100%        100%         -','',
    降sgr(31,'1 of 4 checks failed'),
])#拼成终端正文
终端退出状态={终端输出样本:{'exitCode':1}}#各终端样本退出状态，以输出正文为键；第 66 轮非零退出

#搜索样本（第 67 轮）结构化 grep：按文件分组；truncated 且 total 更大练封顶；超 CHAT_SEARCH_MAX_LINES 练头尾帽。
搜索命中样本=[#按文件分组的 grep 命中
    {'path':'packages/client/ui-primitives/src/SearchBlock.tsx','matches':[
        {'lineNumber':16,'line':'export const DEFAULT_SEARCH_MAX_LINES = 16'},
        {'lineNumber':138,'line':'export function SearchBlock(props: SearchBlockProps) {'},
        {'lineNumber':141,'line':'  const [collapsed, setCollapsed] = useState<ReadonlySet<number>>(() => new Set())'},
    ]},
    {'path':'packages/client/ui-tool/src/client/tool/models/search-card-model.ts','matches':[
        {'lineNumber':45,'line':'export const CHAT_SEARCH_MAX_LINES = 8'},
        {'lineNumber':130,'line':'export function searchCardModel(block: ToolCallBlock): SearchCardModel | null {'},
    ]},
    {'path':'packages/client/ui-tool/src/client/tool/toolviews/search-row.tsx','matches':[
        {'lineNumber':34,'line':'export function SearchRow({ toolName, block, inspect, t }: SearchRowProps) {'},
        {'lineNumber':36,'line':'  const search = searchCardModel(block)'},
        {'lineNumber':56,'line':'      search={search}'},
        {'lineNumber':78,'line':"      yield ctx.slots.register({ name: 'tool.call.toolview', key: 'grep', locale: NS }, SearchRow)"},
    ]},
]#结束搜索命中样本
#面向模型的 grep 正文：Found X of Y / Line N: / 溢出脚（镜像 formatGrepOutput）。
搜索命中正文='\n'.join([#模型可见 grep 正文
    'Found 9 of 42 matches','',
    *[f"{文件['path']}\n"+'\n'.join(f"Line {命中['lineNumber']}: {命中['line']}" for 命中 in 文件['matches']) for 文件 in 搜索命中样本],
    '','(Full grep result stored at: fixture://spill/grep-66. Read it to see every match.)',
])#拼成单字符串
搜索路径样本=[#第 68 轮 glob：扁平路径，truncated 且 total 更大
    'packages/client/ui-primitives/src/SearchBlock.tsx',
    'packages/client/ui-primitives/src/SearchBlock.module.css',
    'packages/client/ui-tool/src/client/tool/models/search-card-model.ts',
    'packages/client/ui-tool/src/client/tool/toolviews/search-row.tsx',
    'packages/client/ui-tool/tests/search-card.client.spec.tsx',
]#结束搜索路径样本
搜索路径正文='\n'.join([#模型可见 glob 正文
    *搜索路径样本,'',
    '(Showing 5 of 23 paths. Full sorted result stored at: fixture://spill/glob-67. Read it to see every path.)',
])#拼成单字符串

#读卡样本：越过偏移的窗口；totalLines 大于窗口；lang=ts 走高亮。
读样本首行=41#窗口首行号
读样本源=[#窗口内源码行
    'export interface ReadBlockProps {','  label?: string | undefined','  lines: readonly ReadBlockLine[]',
    '  totalLines: number','  lang?: string | undefined','  maxLines?: number | undefined',
    '  className?: string | undefined','}','','// A windowed read keeps the file line numbers in the gutter.',
    'const marker = "fixture read sample"',
]#结束读样本源
读样本行=[{'number':读样本首行+下标,'text':文本} for 下标,文本 in enumerate(读样本源)]#带文件行号
读样本路径='packages/client/ui-primitives/src/ReadBlock.tsx'#样本路径
读样本总行=180#文件总行（大于窗口）
读样本正文='\n'.join(f'{读样本首行+下标}: {文本}' for 下标,文本 in enumerate(读样本源))#模型可见 N: 行

#网页搜索轮结构化结果：覆盖有标题+摘要+日期 / 无标题有摘要无日期 / 有标题+日期无摘要；truncated 开封顶。
网页搜索结果={#web 搜索结果
    'answer':'DeepSeek Harness is a plugin-based agent harness on vendored Cordis where **every capability is a plugin**.',
    'sources':[
        {'url':'https://github.com/deepseek-ai/deepseek-harness','title':'DeepSeek Harness — plugin-based agent harness','snippet':'Everything is a plugin: session, tools, agent-loop, and LLM adapters all mount on the same Cordis context.','publishedAt':'2026-07-01'},
        {'url':'https://www.deepseek.com/blog/harness-architecture','snippet':'The capability-seam pattern splits each capability into interface, implementation, and consumer packages.'},
        {'url':'https://docs.deepseek.com/harness/plugins','title':'Writing a harness plugin','publishedAt':'2026-06-15'},
    ],
    'truncated':True,
}#结束网页搜索结果
网页抓取结果={#web 抓取结果
    'url':'https://www.deepseek.com/blog/harness-architecture','statusCode':200,'truncated':False,
}#结束网页抓取结果
夹具图像数据='iVBORw0KGgoAAAANSUhEUgAAAKAAAABaCAYAAAA/xl1SAAAAvklEQVR42u3SMQ0AAAjAMIyhELM4AAe8PD1qYFlk9cCXEAEDYkAwIAYEA2JAMCAGBANiQDAgBgQDYkAwIAYEA2JAMCAGBANiQDAgBgQDYkAwIAYEA2JAMCAGxIBCYEAMCAbEgGBADAgGxIBgQAwIBsSAYEAMCAbEgGBADAgGxIBgQAwIBsSAYEAMCAbEgGBADAgGxIAYEAyIAcGAGBAMiAHBgBgQDIgBwYAYEAyIAcGAGBAMiAHBgBgQDIgB4bYWLb6pnOb1xAAAAABJRU5ErkJggg=='#样本 PNG base64
夹具图像引用={#稳定图片附件引用
    'attachmentId':'fixture:image','mediaType':'image/png','bytes':247,'width':160,'height':90,'name':'fixture-image.png',
}#结束夹具图像引用
_深求={#DeepSeek 推理档
    'efforts':[{'id':'off','name':'Off'},{'id':'high','name':'High'},{'id':'max','name':'Max'}],'defaultEffort':'high',
}
_开求={#OpenAI 推理档
    'efforts':[{'id':'off','name':'Off'},{'id':'medium','name':'Medium'},{'id':'high','name':'High'},{'id':'max','name':'Max'}],'defaultEffort':'medium',
}

def 夹具模型分组():#造模型目录
    """`session.models` 与 `llm.models` 共用；每次调用新拷贝。"""
    return [#两组提供方
        {'id':'deepseek-official','name':'DeepSeek','models':[
            {'id':'deepseek-v4-flash','name':'DeepSeek-V4-Flash','description':'快速响应','reasoning':dict(_深求)},
            {'id':'deepseek-v4-pro','name':'DeepSeek-V4-Pro','description':'复杂任务','reasoning':dict(_深求)},
        ]},
        {'id':'openai','name':'OpenAI','models':[{'id':'gpt-5','name':'GPT-5','reasoning':dict(_开求)}]},
    ]#结束分组

def 夹具用量(轮次,步):#造用量
    """挂在 fixture 助手消息上的确定性提供方账单。"""
    return {#随 turn/step 变化
        'inputTokens':20+轮次%5,'outputTokens':8+步,
        'cacheReadTokens':0 if 轮次==0 else 80,'cacheWriteTokens':4 if 轮次%10==0 else 0,
    }#结束用量

权限预设表={#宿主 PermissionPresetService 默认
    'workspace-write':{'sandbox':'workspace-write','approval':'ask','description':'Write inside the workspace and permitted temporary directories; wider retries require approval.'},
    'danger-full-access':{'sandbox':'danger-full-access','approval':'never','description':'Full file access without approval prompts.'},
}#结束权限预设表

字符每令牌=4#token-meter 固定密度：每 token 字符
块开销=4#块开销
角色开销=4#角色开销

def 取字符串(值,回退=''):#非字符串回退
    """把解析后的 JSON 字段收窄成字符串；非字符串只表示文件内笔误。"""
    return 值 if isinstance(值,str) else 回退#非字符串回退

def 展示调用(名,参数原文):#按工具名造调用卡
    """fixture 展示器注册表（镜像宿主 viewFor）：纯推导，None = 无视图。"""
    try:#参数是文件内手写 JSON
        参数=json.loads(参数原文)#解析
        if not isinstance(参数,dict):#必须是对象
            参数={}#空
    except Exception:#非法 JSON
        return None#无视图
    if 名 in ('fx-bash','bash'):#两名同画终端卡
        return {'card':'terminal','title':取字符串(参数.get('command')),'cwd':取字符串(参数.get('cwd'),'/tmp/fixture'),'description':'fixture 终端样本'}#终端未决
    if 名=='fx-write':#写卡
        return {'card':'diff','title':f"Write {取字符串(参数.get('path'))}",'diffs':[{'path':取字符串(参数.get('path')),'oldText':None,'newText':取字符串(参数.get('content'))}]}#新建
    if 名=='read':#未决读：GENERIC kind=read
        return {'card':'generic','title':f"Read {取字符串(参数.get('file_path'))}",'kind':'read','locations':[{'path':取字符串(参数.get('file_path'))}]}#未决读
    if 名=='edit':#编辑卡
        路径=取字符串(参数.get('file_path'))#路径
        if 路径=='src/config.ts':#双 hunk 标记路径
            return {'card':'diff','title':f'Edit {路径}','diffs':[#两处替换
                {'path':路径,'oldText':'const timeout = 30','newText':'const timeout = 60'},
                {'path':路径,'oldText':'retries: 1','newText':'retries: 3'},
            ]}#结束双 hunk
        return {'card':'diff','title':f'Edit {路径}','diffs':[{'path':路径,'oldText':取字符串(参数.get('old_string')),'newText':取字符串(参数.get('new_string'))}]}#单 hunk
    if 名=='write':#keyed write
        return {'card':'diff','title':f"Write {取字符串(参数.get('file_path'))}",'diffs':[{'path':取字符串(参数.get('file_path')),'oldText':None,'newText':取字符串(参数.get('content'))}]}#写
    if 名=='grep':#未决 grep
        return {'card':'generic','title':f"Grep {取字符串(参数.get('pattern'))}",'kind':'search','rawInput':参数}#generic 搜索
    if 名=='glob':#未决 glob
        return {'card':'generic','title':f"Glob {取字符串(参数.get('pattern'))}",'kind':'search','rawInput':参数}#generic 搜索
    if 名=='web_search':#未决搜索
        return {'card':'generic','title':f"Search {取字符串(参数.get('query'))}",'kind':'search','rawInput':参数}#未决搜索
    if 名=='web_fetch':#未决抓取
        return {'card':'generic','title':f"Fetch {取字符串(参数.get('url'))}",'kind':'fetch','rawInput':参数}#未决抓取
    return None#echo 等：文档化的无视图回退

def 展示结果(名,参数原文,结果正文):#造结果卡
    """按工具名与调用视图造结果卡。"""
    调用=展示调用(名,参数原文)#先看调用卡
    if 调用 is None:#无调用视图则无结果视图
        return None#无
    if 名=='grep':#命中形态
        return {'card':'search','shape':'matches','files':搜索命中样本,'truncated':True,'total':42}#封顶
    if 名=='glob':#路径形态
        return {'card':'search','shape':'paths','paths':搜索路径样本,'truncated':True,'total':23}#封顶
    if 名=='read':#读卡结构化窗口
        return {'card':'read','path':读样本路径,'offset':读样本首行,'lines':读样本行,'totalLines':读样本总行,'lang':'ts','content':[{'type':'text','text':结果正文}]}#读卡
    if 名=='web_search':#搜索结果
        return {'card':'web','kind':'search',**网页搜索结果}#展开样本
    if 名=='web_fetch':#抓取结果
        return {'card':'web','kind':'fetch',**网页抓取结果}#展开样本
    卡=调用.get('card')#调用卡类型
    if 卡=='terminal':#终端结果
        退出=终端退出状态.get(结果正文,{'exitCode':0})#查表或 0
        return {'card':'terminal','output':结果正文,**退出}#终端
    if 卡=='diff':#diff 结果
        return {'card':'diff','diffs':调用.get('diffs')}#回传 diffs
    if 卡=='generic':#正文卡
        return {'card':'generic','content':[{'type':'text','text':结果正文}]}#正文
    return None#未知卡

def 视图为(事件,日志):#事件 → 工具视图
    """宿主侧 viewFor 镜像：tool/call 用自身参数；tool/result 回扫找配对。"""
    类型=事件.get('type') if isinstance(事件,dict) else getattr(事件,'type',None)#类型
    数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',None)#数据
    if 类型=='tool/call':#调用
        视图=展示调用(数据.get('name'),数据.get('arguments',''))#按名+参
        return None if 视图 is None else {'for':'call','view':视图}#包一层
    if 类型=='tool/result':#结果
        消息=数据.get('message') if isinstance(数据,dict) else {}#工具结果消息
        来源=消息.get('source') if isinstance(消息,dict) else {}#来源
        调用标识=str(消息.get('callId') or (来源.get('callId') if isinstance(来源,dict) else '') or '')#配对键
        for 下标 in range(len(日志)-1,-1,-1):#从尾回扫
            候选=日志[下标]#候选
            候类型=候选.get('type') if isinstance(候选,dict) else None#类型
            候数据=候选.get('data') if isinstance(候选,dict) else {}#数据
            if 候类型=='tool/call' and str(候数据.get('callId',''))==调用标识:#配对
                内容=消息.get('content') if isinstance(消息,dict) else []#内容块
                结果正文=''.join(块.get('text','') if isinstance(块,dict) and 块.get('type')=='text' else '' for 块 in (内容 or []))#抽文本
                视图=展示结果(候数据.get('name'),候数据.get('arguments',''),结果正文)#造结果卡
                return None if 视图 is None else {'for':'result','view':视图}#包一层
        return None#跨页未配对
    return None#其它事件无工具视图

def 折计划(日志):#折计划模式
    """名为 plan 的 command/run 设 wanted；plan/mode 提交并清空。"""
    活动=False#已提交
    想要=None#命令想要、尚未提交
    for 事件 in 日志:#顺序折
        类型=事件.get('type') if isinstance(事件,dict) else None#类型
        数据=事件.get('data') if isinstance(事件,dict) else {}#数据
        if 类型=='command/run' and 数据.get('name')=='plan':#计划命令
            参数=数据.get('args')#原始输入
            if not isinstance(参数,str):#非字符串跳过
                continue#跳过
            想要=参数.strip()!='off'#off 关，其它开
        elif 类型=='plan/mode':#提交
            活动=数据.get('active') is True#新值
            想要=None#清未决
    return {'active':活动,'pending':想要 is not None and 想要!=活动,'wanted':想要}#pending = 想要但未生效

def 计划视图于(日志):#投影用计划
    """计划投影在全日志上的线上视图。"""
    计划=折计划(日志)#折一次
    return {'active':计划['active'],'pending':计划['pending']}#丢掉 wanted

def 权限选择于(日志):#权限 select
    """宿主权限单元平行：折三个旋钮事件，相对 fixture 默认推导 select。"""
    预设=None#显式预设
    沙箱='workspace-write'#默认沙箱
    审批='ask'#默认审批
    for 事件 in 日志:#顺序折旋钮
        类型=事件.get('type') if isinstance(事件,dict) else None#类型
        数据=事件.get('data') if isinstance(事件,dict) else {}#数据
        if 类型=='permission/preset':#预设
            预设=数据.get('preset')#点名
        elif 类型=='sandbox/mode':#沙箱
            沙箱=数据.get('mode','workspace-write')#模式
        elif 类型=='approval/policy':#审批
            审批=数据.get('policy','ask')#策略
    def 贴合(规格):#旋钮是否贴合预设
        return 规格['sandbox']==沙箱 and 规格['approval']==审批#双匹配
    当前值='custom'#对不上任何预设
    点名规格=权限预设表.get(预设) if 预设 is not None else None#点名的预设规格
    if 预设 is not None and 点名规格 is not None and 贴合(点名规格):#点名且旋钮仍贴合
        当前值=预设#用点名
    else:#否则按旋钮反查
        for 名称,规格 in 权限预设表.items():#扫表
            if 贴合(规格):#第一贴合
                当前值=名称#记下
                break#停
    选项=[{'value':值,'name':值,'description':规格['description']} for 值,规格 in 权限预设表.items()]#预设
    if 当前值=='custom':#可选 Custom
        选项.append({'value':'custom','name':'Custom','description':'Current sandbox and approval settings do not match a preset.'})#自定义
    return {'options':选项,'currentValue':当前值}#select 载荷

def 是否令牌增量(块):#是否 token 增量块
    """对齐 isTokenDelta：带文本增量的块。"""
    if not isinstance(块,dict):#非映射
        return False#否
    return 块.get('type') in ('text-delta','reasoning-delta','tool-call-delta')#增量类

def 用量样本于(事件):#抽用量样本
    """从 assistant/chunk(usage) 或 assistant/message 读提供方用量样本。"""
    类型=事件.get('type') if isinstance(事件,dict) else None#类型
    数据=事件.get('data') if isinstance(事件,dict) else {}#数据
    if not isinstance(数据,dict):#无数据
        return None#无
    用量=None#待填
    if 类型=='assistant/chunk':#chunk 用量
        块=数据.get('chunk') if isinstance(数据.get('chunk'),dict) else {}#块
        if 块.get('type')=='usage':#用量块
            用量=块.get('usage')#用量
    elif 类型=='assistant/message':#定稿消息用量
        用量=数据.get('usage')#用量
    if 用量 is None or 数据.get('turn') is None or 数据.get('step') is None:#缺字段
        return None#无
    return {'turn':数据['turn'],'step':数据['step'],'usage':用量}#齐才成样本

def 令牌用量于(日志):#折用量合计
    """token-meter「末样本替换」用量投影的 fixture 平行。"""
    合计={'uncachedInputTokens':0,'outputTokens':0,'cacheReadTokens':0,'cacheWriteTokens':0}#累计
    上次=None#同 turn+step 的上一份桶
    for 事件 in 日志:#顺序折
        样本=用量样本于(事件)#抽样本
        if 样本 is None:#非用量事件
            continue#跳过
        用量=样本['usage'] if isinstance(样本['usage'],dict) else {}#用量
        桶={#本样本桶
            'uncachedInputTokens':用量.get('inputTokens',0),
            'outputTokens':用量.get('outputTokens',0),
            'cacheReadTokens':用量.get('cacheReadTokens') or 0,
            'cacheWriteTokens':用量.get('cacheWriteTokens') or 0,
        }#结束桶
        先前=上次['buckets'] if 上次 is not None and 上次['turn']==样本['turn'] and 上次['step']==样本['step'] else None#同一步则替换
        for 键 in 合计:#差额累加
            合计[键]+=桶[键]-(先前[键] if 先前 else 0)#差额
        上次={'turn':样本['turn'],'step':样本['step'],'buckets':桶}#记下
    return 合计#合计

def 会话统计于(日志):#会话统计
    """session-stats 全日志计数与墙钟折的 fixture 平行。"""
    值={'turns':0,'steps':0,'llmMs':0,'toolMs':0,'ttftMs':0,'ttftSteps':0,'decodeMs':0,'decodeTokens':0}#累加器
    上轮=None#已计过的轮
    开步=None#未关的步
    未决调用={}#callId → 派出时刻
    for 事件 in 日志:#顺序折
        类型=事件.get('type') if isinstance(事件,dict) else None#类型
        数据=事件.get('data') if isinstance(事件,dict) else {}#数据
        时刻=事件.get('time',0) if isinstance(事件,dict) else 0#时刻
        if 类型=='step/start':#开步
            开步={'turn':数据.get('turn'),'step':数据.get('step'),'startTime':时刻,'firstTokenTime':None}#开步
        elif 类型=='assistant/chunk':#chunk
            if 开步 is not None and 开步['turn']==数据.get('turn') and 开步['step']==数据.get('step') and 开步['firstTokenTime'] is None and 是否令牌增量(数据.get('chunk')):#首 token
                开步['firstTokenTime']=时刻#记 TTFT
        elif 类型=='assistant/message':#定稿
            if 开步 is None or 开步['turn']!=数据.get('turn') or 开步['step']!=数据.get('step'):#对不上
                pass#忽略
            else:#对齐开步
                值['llmMs']+=max(0,时刻-开步['startTime'])#LLM 墙钟
                if 开步['firstTokenTime'] is not None:#有首 token
                    值['ttftMs']+=max(0,开步['firstTokenTime']-开步['startTime'])#累加 TTFT
                    值['ttftSteps']+=1#计步
                    用量=数据.get('usage') if isinstance(数据.get('usage'),dict) else {}#用量
                    输出=用量.get('outputTokens')#输出 token
                    if isinstance(输出,(int,float)) and 输出==输出 and 输出>=0:#合法
                        值['decodeMs']+=max(0,时刻-开步['firstTokenTime'])#解码墙钟
                        值['decodeTokens']+=int(输出)#解码 token
                开步=None#步已定稿
        elif 类型=='tool/call':#调用
            未决调用[数据.get('callId')]=时刻#记下派出
        elif 类型=='tool/result':#结算
            消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}#消息
            来源=消息.get('source') if isinstance(消息.get('source'),dict) else {}#来源
            调用标识=消息.get('callId') or 来源.get('callId')#配对
            派出=未决调用.pop(调用标识,None)#派出时刻
            if 派出 is not None:#已配对
                值['toolMs']+=max(0,时刻-派出)#工具墙钟
        elif 类型=='step/end':#关步
            if 数据.get('turn')!=上轮:#新轮
                值['turns']+=1#计轮
                上轮=数据.get('turn')#记下
            值['steps']+=1#计步
            开步=None#关步
        elif 类型=='turn/end':#轮结束
            未决调用.clear()#丢未结算调用
    return 值#统计

def 估算夹具内容(块们):#启发式计价
    """用 token-meter 的固定密度启发式给 fixture 内容标价。"""
    def 密度价(文本):#按字符密度
        return (len(文本)+字符每令牌-1)//字符每令牌 if 文本 else 0#向上取整
    令牌=0#累加
    for 块 in 块们 or []:#逐块
        if not isinstance(块,dict):#非映射
            continue#跳过
        类型=块.get('type')#类型
        if 类型 in ('text','reasoning'):#正文/思考
            令牌+=密度价(块.get('text',''))+块开销#文本 + 块开销
        elif 类型=='tool-call':#调用
            令牌+=密度价(块.get('name',''))+密度价(块.get('arguments',''))+块开销#名+参
        elif 类型=='tool-result':#嵌套结果
            令牌+=估算夹具内容(块.get('content') or [])+块开销#递归
        else:#扩展块走 JSON
            令牌+=密度价(json.dumps(块,ensure_ascii=False))+块开销#JSON
    return 令牌#估算

def 折表面(日志):#折当前表面节点
    """简化 foldSurface：append/replace 消息节点；返回 {nodes: seq 列表}。"""
    节点=[]#当前表面 seq
    for 事件 in 日志:#顺序
        if not isinstance(事件,dict):#非映射
            continue#跳过
        类型=事件.get('type')#类型
        序号=事件.get('seq')#seq
        操作=事件.get('surfaceOp')#表面操作
        if 类型 in ('user/message','assistant/message','tool/result') and 操作=='append':#追加
            节点.append(序号)#挂上
        elif 类型 in ('user/message','assistant/message','tool/result') and 操作=='replace':#替换
            if 节点:#有节点
                节点[-1]=序号#替换末
            else:#空
                节点.append(序号)#当追加
    return {'nodes':节点}#表面

def 派生事件消息(事件):#抽消息
    """简化 deriveEventMessage：从用户/助手/工具结果抽出可计价消息。"""
    if not isinstance(事件,dict):#非映射
        return None#无
    类型=事件.get('type')#类型
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
    if 类型=='user/message':#用户
        return {'role':'user','content':数据.get('content') or []}#用户消息
    if 类型=='assistant/message':#助手
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}#消息
        return {'role':'assistant','content':消息.get('content') or []}#助手
    if 类型=='tool/result':#工具结果
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}#消息
        return {'role':'tool','content':消息.get('content') or []}#工具
    return None#其它无

def 上下文组成于(日志):#启发式组成
    """token-meter 启发式上下文组成投影的 fixture 平行。"""
    头事件=None#最近 request/header
    for 事件 in reversed(日志):#从尾
        if isinstance(事件,dict) and 事件.get('type')=='request/header':#头
            头事件=事件#记下
            break#停
    头=None#头载荷
    if 头事件 is not None:#有头
        数据=头事件.get('data') if isinstance(头事件.get('data'),dict) else {}#数据
        头=数据.get('header') if isinstance(数据.get('header'),dict) else 数据#头
    消息令牌=0#表面消息合计
    for 序号 in 折表面(日志)['nodes']:#当前表面节点
        if not isinstance(序号,int) or 序号<0 or 序号>=len(日志):#空洞
            continue#跳过
        消息=派生事件消息(日志[序号])#抽消息
        if 消息 is not None:#可计价
            消息令牌+=估算夹具内容(消息.get('content') or [])+角色开销#计价
    系统令牌=0#系统
    工具令牌=0#工具
    if isinstance(头,dict):#有头
        系统=头.get('system')#系统
        if isinstance(系统,str):#有系统
            系统令牌=(len(系统)+字符每令牌-1)//字符每令牌+角色开销#系统+角色
        工具=头.get('tools')#工具
        if isinstance(工具,list) and 工具:#有工具
            工具令牌=(len(json.dumps(工具,ensure_ascii=False))+字符每令牌-1)//字符每令牌+块开销#工具 JSON
    return {'systemTokens':系统令牌,'toolsTokens':工具令牌,'messageTokens':消息令牌}#三桶

def 最近请求上下文(日志):#最近 request/context
    """最近一条仅日志的路由上下文；任何请求跑过之前为 None。"""
    for 事件 in reversed(日志):#从尾找
        if isinstance(事件,dict) and 事件.get('type')=='request/context':#命中
            数据=事件.get('data')#data 即上下文
            return 数据 if isinstance(数据,dict) else None#上下文
    return None#没有

def 上下文压力于(日志):#压力投影
    """最近一次提供方报告的 prompt 尺寸配最近记录的容量。"""
    压力令牌=None#末样本 prompt 尺寸
    for 事件 in 日志:#扫到最后一条用量
        样本=用量样本于(事件)#抽
        if 样本 is None:#非用量
            continue#跳过
        用量=样本['usage'] if isinstance(样本['usage'],dict) else {}#用量
        压力令牌=用量.get('inputTokens',0)+(用量.get('cacheReadTokens') or 0)+(用量.get('cacheWriteTokens') or 0)#输入+缓存
    结果={}#可缺字段
    if 压力令牌 is not None:#有压力
        结果['pressureTokens']=压力令牌#压力
    上下文=最近请求上下文(日志)#最近容量
    if isinstance(上下文,dict) and 上下文.get('contextWindow') is not None:#有容量
        结果['contextWindow']=上下文['contextWindow']#容量
    return 结果#压力

def 回扫待办(日志):#回扫待办
    """最近 todo/write 且其后无 turn/start；新轮退役上一计划。"""
    for 下标 in range(len(日志)-1,-1,-1):#从尾
        事件=日志[下标]#候选
        if not isinstance(事件,dict):#空洞
            continue#跳过
        if 事件.get('type')=='turn/start':#新轮退役
            return None#已退役
        if 事件.get('type')=='todo/write':#站住
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
            return 数据.get('todos')#待办列表
    return None#从未写过

def 回扫目标(日志):#回扫目标
    """GoalService 对 goal/change 整值 last-wins；clear 回 None。"""
    for 下标 in range(len(日志)-1,-1,-1):#从尾
        事件=日志[下标]#候选
        if not isinstance(事件,dict) or 事件.get('type')!='goal/change':#非目标变更
            continue#跳过
        变更=事件.get('data') if isinstance(事件.get('data'),dict) else {}#变更
        if 变更.get('operation')=='clear':#清除
            return None#已清除
        return {#站住
            'goal':变更.get('goal'),
            'roundsStarted':变更.get('roundsStarted',0),
            'createdAt':变更.get('createdAt',0),
            'updatedAt':变更.get('updatedAt',0),
        }#结束投影
    return None#从未有

def 投影值于(日志):#基线投影包
    """全日志上各投影键的当前整值。"""
    值={}#待填
    for 事件 in reversed(日志):#最近标题
        if isinstance(事件,dict) and 事件.get('type')=='session/title':#有标题
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
            值['title']=数据.get('title')#标题字符串
            break#停
    值['todos']=回扫待办(日志)#无站立计划时为 None（上游 null）
    值['permissions']=权限选择于(日志)#权限
    值['plan']=计划视图于(日志)#计划
    值['goal']=回扫目标(日志)#目标
    值['tokenUsage']=令牌用量于(日志)#用量
    值['contextPressure']=上下文压力于(日志)#压力
    值['contextBreakdown']=上下文组成于(日志)#组成
    值['sessionStats']=会话统计于(日志)#统计
    值['imageLimits']={#图像上限（镜像 attachment-local 默认）
        'maxImageBytes':5*1024*1024,'maxImagesPerMessage':20,
        'maxMessageImageBytes':100*1024*1024,'maxImagePixels':40_000_000,
        'mediaTypes':['image/png','image/jpeg','image/webp','image/gif'],
    }#结束 imageLimits
    return 值#整包

def 投影帧于(会话标识,日志,事件):#事件 → 投影帧
    """宿主推帧平行：给定事件推进了哪些键，就为每个键发一帧 session/projection。"""
    类型=事件.get('type') if isinstance(事件,dict) else None#事件类型
    序号=事件.get('seq') if isinstance(事件,dict) else 0#seq
    帧们=[]#收集
    if 用量样本于(事件) is not None:#有用量
        帧们.append({'type':'session/projection','sessionId':会话标识,'key':'tokenUsage','value':令牌用量于(日志),'seq':序号})#用量帧
        帧们.append({'type':'session/projection','sessionId':会话标识,'key':'contextPressure','value':上下文压力于(日志),'seq':序号})#压力帧
    if 类型=='request/context':#容量变化
        帧们.append({'type':'session/projection','sessionId':会话标识,'key':'contextPressure','value':上下文压力于(日志),'seq':序号})#压力
    if 类型 in ('request/header','user/message','assistant/message','tool/result'):#推进组成
        帧们.append({'type':'session/projection','sessionId':会话标识,'key':'contextBreakdown','value':上下文组成于(日志),'seq':序号})#组成
    if 类型 in ('assistant/message','tool/result','step/end'):#统计触发
        帧们.append({'type':'session/projection','sessionId':会话标识,'key':'sessionStats','value':会话统计于(日志),'seq':序号})#统计
    if 帧们:#已有批量帧则不再走单键路径
        return 帧们#批量
    if 类型=='session/title':#标题
        值们=投影值于(日志)#现算
        if 'title' not in 值们:#防守
            return []#空
        return [{'type':'session/projection','sessionId':会话标识,'key':'title','value':值们['title'],'seq':序号}]#标题帧
    if 类型=='goal/change':#目标
        return [{'type':'session/projection','sessionId':会话标识,'key':'goal','value':回扫目标(日志),'seq':序号}]#目标帧
    if 类型 in ('todo/write','turn/start'):#待办
        return [{'type':'session/projection','sessionId':会话标识,'key':'todos','value':回扫待办(日志),'seq':序号}]#待办帧
    if 类型 in ('permission/preset','sandbox/mode','approval/policy'):#权限
        return [{'type':'session/projection','sessionId':会话标识,'key':'permissions','value':权限选择于(日志),'seq':序号}]#权限帧
    数据=事件.get('data') if isinstance(事件,dict) else {}#命令数据
    if 类型=='plan/mode' or (类型=='command/run' and isinstance(数据,dict) and 数据.get('name')=='plan' and isinstance(数据.get('args'),str)):#计划选择
        return [{'type':'session/projection','sessionId':会话标识,'key':'plan','value':计划视图于(日志),'seq':序号}]#计划帧
    return []#本事件不推进任何键

def 分页于(日志,之前序号,最多消息):#一页历史
    """消息边界分页：从尾往回数 maxMessages 条消息，切在 turn/start 边界。"""
    末=len(日志) if 之前序号 is None else max(0,min(之前序号,len(日志)))#右开
    起=0#默认从头
    消息数=0#已数消息
    for 下标 in range(末-1,-1,-1):#从尾往回数
        事件=日志[下标]#候选
        类型=事件.get('type') if isinstance(事件,dict) else None#类型
        if 类型 in ('user/message','assistant/message'):#计消息
            消息数+=1#加一
        if 类型=='turn/start' and 消息数>=最多消息:#够数且在轮边界
            起=下标#切在此
            break#停
    条目们=[]#本页
    for 事件 in 日志[起:末]:#窗口内
        视图=视图为(事件,日志)#分页时视图
        条目们.append({'event':事件} if 视图 is None else {'event':事件,'view':视图})#可无视图
    return {'events':条目们,'hasMore':起>0}#start>0 表示还有更早

def 日志引用附件(日志,附件标识):#深搜引用
    """宿主会话范围附件授权的 fixture 镜像。"""
    def 访问(值):#递归
        if isinstance(值,list):#数组任一
            return any(访问(项) for 项 in 值)#任一
        if not isinstance(值,dict):#非对象
            return False#否
        if 值.get('attachmentId')==附件标识:#命中
            return True#是
        return any(访问(子) for 子 in 值.values())#下钻
    return any(访问(事件.get('data') if isinstance(事件,dict) else None) for 事件 in 日志)#任一事件

def 检索块文本(块):#块 → 文本
    """session-query 用的第一方消息抽取。"""
    if not isinstance(块,dict):#非映射
        return []#空
    类型=块.get('type')#类型
    if 类型=='text':#正文
        return [块.get('text','')]#正文
    if 类型=='reasoning':#思考不进检索
        return []#空
    if 类型=='tool-call':#名+参
        return [块.get('name',''),块.get('arguments','')]#名+参
    if 类型=='tool-result':#递归
        片段=[]#收集
        for 子 in 块.get('content') or []:#子块
            片段.extend(检索块文本(子))#递归
        return 片段#片段
    return []#扩展块不检索

def 检索事件文本(事件):#事件 → 检索正文
    """一条当前表面的用户/助手文档（若可检索）。"""
    if not isinstance(事件,dict):#非映射
        return ''#空
    类型=事件.get('type')#类型
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
    内容=None#待填
    if 类型=='user/message':#用户
        内容=数据.get('content')#内容
    elif 类型=='assistant/message':#助手
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}#消息
        内容=消息.get('content')#内容
    if 内容 is None:#不可检索
        return ''#空
    片段=[]#收集
    for 块 in 内容:#逐块
        for 部 in 检索块文本(块):#片段
            部=部.strip() if isinstance(部,str) else ''#去空白
            if 部:#非空
                片段.append(部)#收下
    return '\n'.join(片段)#拼非空片段

def _是词基(字符):#字母/数字/私用
    """FTS unicode61 词基近似。"""
    类=unicodedata.category(字符)#Unicode 类
    return 类.startswith('L') or 类.startswith('N') or 类=='Co'#字母/数字/私用

def 检索令牌跨度(值):#切 token
    """SQLite FTS5 unicode61 token 边界的浏览器安全近似。"""
    import re as 正则#空白归一
    文本=正则.sub(r'\s+',' ',值 or '').strip()#空白归一
    字符们=list(文本)#按 code point（BMP 内等同）
    令牌们=[]#收集
    起点=None#当前 token 起点
    原文=''#当前 token 原文
    def 收尾(终点):#收一个 token
        nonlocal 起点,原文#可变
        if 起点 is not None:#有进行中的
            折叠=unicodedata.normalize('NFD',原文)#去标记前
            折叠=''.join(字 for 字 in 折叠 if unicodedata.category(字)!='Mn').lower()#去 Mn、小写
            if 折叠!='':#非空才收
                令牌们.append({'value':折叠,'start':起点,'end':终点})#收下
        起点=None#清空
        原文=''#清空
    for 下标,字符 in enumerate(字符们):#逐码点
        基=unicodedata.normalize('NFD',字符)#去标记前
        基=''.join(字 for 字 in 基 if unicodedata.category(字)!='Mn')#去 Mn
        if 基=='':#纯标记
            if 起点 is not None:#挂在当前 token
                原文+=字符#追加
            continue#不单独成 token
        if all(_是词基(字) for 字 in 基):#字母/数字/私用
            if 起点 is None:#开 token
                起点=下标#起点
            原文+=字符#追加
        else:#分隔符
            收尾(下标)#在此切开
    收尾(len(字符们))#收尾
    return {'text':文本,'tokens':令牌们}#规范化文本 + token

def 短语匹配(文档令牌,短语):#短语匹配
    """数精确相邻 token 短语出现次数，并保留首次展示跨度。"""
    if not 短语 or len(短语)>len(文档令牌):#空或过长
        return {'count':0,'start':0,'end':0}#空
    次数=0#次数
    首次起=0#首次起
    首次止=0#首次止
    for 起 in range(0,len(文档令牌)-len(短语)+1):#滑窗
        if not all(文档令牌[起+偏].get('value')==词 for 偏,词 in enumerate(短语)):#不贴合
            continue#下一窗
        次数+=1#计一次
        if 次数==1:#记下首次跨度
            首次起=文档令牌[起].get('start',0)#起
            首次止=文档令牌[起+len(短语)-1].get('end',首次起)#止
    return {'count':次数,'start':首次起,'end':首次止}#结果

def 检索摘录(值,命中起,命中止):#侧栏摘录
    """以命中为中心的 fixture 摘录，按 Unicode code point 限界。"""
    字符们=list(值 or '')#按码点
    if len(字符们)<=120:#短则全文
        return 值 or ''#全文
    界起=min(max(0,命中起),len(字符们)-1)#夹起点
    界止=min(len(字符们),max(界起+1,命中止))#夹终点
    中心=(界起+界止)//2#命中中心
    起=min(len(字符们)-118,max(0,中心-118//2))#窗口起
    止=起+118#默认窗长
    if 起==0:#贴头
        止=119#头窗稍长
    elif 止==len(字符们):#贴尾
        起=len(字符们)-119#尾窗稍长
    return f"{'…' if 起>0 else ''}{''.join(字符们[起:止])}{'…' if 止<len(字符们) else ''}"#省略号

def 比较检索候选(甲,乙):#检索排序
    """镜像 session-query-sqlite：命中多、文档长、时间新、会话 id、seq 倒序。"""
    if 甲['matchCount']!=乙['matchCount']:#次数降序
        return 乙['matchCount']-甲['matchCount']#降序
    if 甲['documentLength']!=乙['documentLength']:#更长优先
        return 甲['documentLength']-乙['documentLength']#升长度差（更长优先 → 甲-乙 负？上游 b-a 对 length 是 a-b）
    if 甲['time']!=乙['time']:#更新优先
        return 乙['time']-甲['time']#时间降序
    if 甲['sessionId']!=乙['sessionId']:#会话 id 升序
        return -1 if 甲['sessionId']<乙['sessionId'] else 1#升序
    return 乙['seq']-甲['seq']#同会话 seq 倒序

#供历史叶复用检索上限（避免循环导入时也可直接读本模块常量）
检索结果上限=会话搜索结果上限#再导出语义锚
