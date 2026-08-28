"""面向模型的前台 Ralph 循环，叠在工作流与子智能体缝上。一份固定脚本每轮启动一个全新的结构化输出子运行，只在它们之间携带不可变目标与有界交接。"""
import json#结果与交接 JSON 序列化
import math#安全整数判定
from ...依赖.schemastery import 路径上节点,字符串字段,整数字段#配置字段
from ...内核.工具 import 定义工具#导入工具定义辅助
__all__=[#仅中文公开名；Cordis 英文槽不入表
    '名称','注入','配置','拉尔夫元数据','拉尔夫脚本','取字段','是否安全整数',
    '落实配置','落实轮数上限','要求全新提供方','是否记录','归一化文本','归一化列表',
    '读报告','读运行结果','停止原因错误','约束结果','渲染结果','渲染轮次失败',
    '展示调用','展示结果','错误','应用',
]#公开面结束

名称='tool-ralph'#Cordis 插件名
注入=['tools','workflowEngine','subagents','systemPrompt']#依赖工具、工作流引擎、子智能体与系统提示词
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
配置=路径上节点({#固定 Ralph 工作流的部署政策
    'subagentProvider':字符串字段(默认值='spawn'),#每轮使用的全新结构化输出提供方（默认 spawn）
    'maxRounds':整数字段(步进=1,最小=1,默认值=256),#一次调用轮数的默认值与部署上限（默认 256）
    'maxHandoffChars':整数字段(步进=1,最小=1,默认值=16_384),#一份结构化交接的最大序列化字符数（默认 16384）
    'maxResultChars':整数字段(步进=1,最小=1,默认值=16_384),#面向父方的成功终态文本最大字符数（默认 16384）
})#结束配置模式
Config=配置#Cordis 配置模式

拉尔夫元数据={#固定工作流身份
    'name':'ralph-loop',#工作流名
    'description':'Iterate toward one objective with a fresh child and bounded structured handoff per round.',#描述
    'phases':[{'title':'Fresh-agent rounds','detail':'One clean child context per Ralph round.'}],#阶段声明
}#结束固定身份
# 固定的、部署所有的编排。模型只提供数据；它改不了循环、提供方路由、模式或交接校验。字面量保持原文。
拉尔夫脚本=r'''
const reportSchema = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['continue', 'complete', 'blocked'] },
    summary: { type: 'string' },
    evidence: { type: 'array', items: { type: 'string' } },
    nextSteps: { type: 'array', items: { type: 'string' } },
    blocker: { type: 'string' },
  },
  required: ['status', 'summary', 'evidence', 'nextSteps', 'blocker'],
  additionalProperties: false,
}

function normalizedText(value) {
  return typeof value === 'string' && value.length > 0 && value === value.trim()
}

function normalizedList(value) {
  return Array.isArray(value) && value.every(normalizedText)
}

function validateReport(report) {
  if (report === null || typeof report !== 'object' || Array.isArray(report)) {
    throw new Error('Ralph child returned no structured round report')
  }
  if (!normalizedText(report.summary)) {
    throw new Error('Ralph round report summary must be non-empty and normalized')
  }
  if (!normalizedList(report.evidence) || !normalizedList(report.nextSteps)) {
    throw new Error('Ralph round report evidence and nextSteps must contain only non-empty normalized strings')
  }
  if (typeof report.blocker !== 'string' || report.blocker !== report.blocker.trim()) {
    throw new Error('Ralph round report blocker must be a normalized string')
  }
  switch (report.status) {
    case 'continue':
      if (report.nextSteps.length === 0 || report.blocker !== '') {
        throw new Error('a continuing Ralph report needs nextSteps and an empty blocker')
      }
      break
    case 'complete':
      if (report.evidence.length === 0 || report.nextSteps.length !== 0 || report.blocker !== '') {
        throw new Error('a complete Ralph report needs evidence, no nextSteps, and an empty blocker')
      }
      break
    case 'blocked':
      if (!normalizedText(report.blocker)) {
        throw new Error('a blocked Ralph report needs a concrete blocker')
      }
      break
    default:
      throw new Error('Ralph round report status is invalid')
  }
  const serialized = JSON.stringify(report)
  if (serialized.length > args.maxHandoffChars) {
    throw new Error('Ralph round report exceeds maxHandoffChars (' + serialized.length + ' > ' + args.maxHandoffChars + ')')
  }
  return report
}

let previous
phase('Fresh-agent rounds')
for (let round = 1; round <= args.maxRounds; round += 1) {
  const prior = previous === undefined ? '(none — this is the first round)' : JSON.stringify(previous)
  const prompt = [
    'You are one fresh worker in a foreground Ralph loop. You receive no parent conversation and no prior child session. Do not call the ralph tool: this round already is its worker.',
    'Immutable objective:\n' + args.objective,
    'Ralph round: ' + round + ' of ' + args.maxRounds + '.',
    'The shared workspace and its current working tree are the long-term memory and source of truth. Inspect them before acting, preserve existing work, perform concrete in-scope work, and verify what you change. Treat the previous report only as a bounded handoff; confirm it against the workspace.',
    'Previous structured handoff:\n' + prior,
    'Return one report with exact normalized strings. Use status continue with at least one nextSteps entry while useful work remains; complete only with concrete evidence and no nextSteps; blocked only when no meaningful progress is possible without human input or an external-state change. blocker must be empty unless blocked.',
  ].join('\n\n')
  const rawReport = await agent(prompt, {
    label: 'Ralph round ' + round,
    phase: 'Fresh-agent rounds',
    schema: reportSchema,
  })
  if (rawReport === null) {
    return { status: 'round-failed', roundsStarted: round, lastReport: previous ?? null }
  }
  const report = validateReport(rawReport)
  if (report.status === 'complete') return { status: 'complete', roundsStarted: round, report }
  if (report.status === 'blocked') return { status: 'blocked', roundsStarted: round, report }
  previous = report
}
return { status: 'budget-limited', roundsStarted: args.maxRounds, report: previous }
'''#部署所有的固定编排脚本，字面量保持原文
描述=(#面向模型的工具描述
    'Run a foreground fresh-agent Ralph loop toward one immutable objective. '#面向模型的工具描述
    +'Use only when the direct human explicitly asks for Ralph or fresh-agent iteration. Each round '#仅在用户明确要求时使用
    +'opens a new child with no parent conversation or prior child session; the shared workspace is '#每轮新开子运行
    +'long-term memory, and only a bounded structured report crosses rounds. The call returns when '#有界交接
    +'a worker reports completion or a concrete blocker, or at the round limit. Ordinary long-running same-session work '#何时返回
    +'belongs to goal tools.'#普通长任务走 goal 工具
)#描述结束
截断标记='\n… [truncated]'#截断标记
拉尔夫输出属性={#结构化输出字段
    'runId':{'type':'string','required':True},#运行标识
    'agentsStarted':{'type':'integer','required':True},#智能体计数
    'result':{'type':'json','required':True},#终态 JSON
}#推断为只读字段表
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否安全整数(值):#对齐 JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是安全整数
    if isinstance(值,int):#整数
        return -(2**53)<值<(2**53)#安全整数范围
    if isinstance(值,float):#浮点
        if not 值.is_integer():#非整值
            return False#不是整数
        return math.isfinite(值) and -(2**53)<值<(2**53)#有限且在安全范围
    return False#其它类型

def 落实配置(配置值):#即便调用方不经 Loader 归一化就调 apply()，也要校验默认值
    """解析并校验部署配置。"""
    提供方=取字段(配置值,'subagentProvider')#读提供方
    if 提供方 is None:#缺省
        提供方='spawn'#缺省 spawn
    轮数上限=取字段(配置值,'maxRounds')#读轮数上限
    if 轮数上限 is None:#缺省
        轮数上限=256#缺省 256
    交接上限=取字段(配置值,'maxHandoffChars')#读交接上限
    if 交接上限 is None:#缺省
        交接上限=16_384#缺省 16384
    结果上限=取字段(配置值,'maxResultChars')#读结果上限
    if 结果上限 is None:#缺省
        结果上限=16_384#缺省 16384
    if len(提供方)==0 or 提供方!=提供方.strip():#空或未归一化
        raise TypeError('subagentProvider must be a non-empty normalized string')#提供方名无效
    if (not 是否安全整数(轮数上限)) or 轮数上限<1:#不是从 1 起的安全整数
        raise TypeError('maxRounds must be a positive safe integer')#轮数无效
    if (not 是否安全整数(交接上限)) or 交接上限<1:#不是从 1 起的安全整数
        raise TypeError('maxHandoffChars must be a positive safe integer')#交接上限无效
    if (not 是否安全整数(结果上限)) or 结果上限<1:#不是从 1 起的安全整数
        raise TypeError('maxResultChars must be a positive safe integer')#结果上限无效
    return {#返回已解析配置
        'subagentProvider':提供方,#子智能体提供方
        'maxRounds':轮数上限,#轮数上限
        'maxHandoffChars':交接上限,#交接字符上限
        'maxResultChars':结果上限,#结果字符上限
    }#结束已解析配置

def 落实轮数上限(请求值,天花板):#把模型选的上限对上部署天花板
    """解析本次轮数上限。"""
    值=天花板 if 请求值 is None else 请求值#未请求则用部署上限
    if (not 是否安全整数(值)) or 值<1:#不是从 1 起的安全整数
        raise TypeError('Ralph maxRounds must be a positive safe integer')#轮数无效
    if 值>天花板:#超过部署上限
        raise TypeError('Ralph maxRounds '+str(值)+' exceeds the deployment ceiling '+str(天花板))#说明超限
    return 值#返回请求值

def 要求全新提供方(上下文,提供方名):#要求配置的路由真的是全新的结构化子运行
    """校验全新结构化提供方。"""
    提供方=上下文.subagents.getProvider(提供方名)#按名查找提供方
    if 提供方 is None:#未登记
        raise 错误('Ralph subagent provider "'+提供方名+'" is not registered')#找不到提供方
    能力=取字段(提供方,'capabilities')#读能力表
    if not 取字段(能力,'outputSchema'):#不支持结构化输出
        raise 错误('Ralph subagent provider "'+提供方名+'" does not support structured output')#缺少 outputSchema
    if 取字段(提供方,'inheritsParentContext'):#会继承父上下文
        raise 错误('Ralph subagent provider "'+提供方名+'" inherits parent context; Ralph requires a fresh provider')#Ralph 要求全新提供方
    return 提供方#返回已校验提供方

def 是否记录(值):#判断是否为普通对象
    """判断是否为非 null 非数组的映射。"""
    return isinstance(值,dict)#Python 侧以 dict 表示普通对象

def 归一化文本(值):#判断是否为非空且已 trim 的字符串
    """判断是否为非空且已 trim 的字符串。"""
    return isinstance(值,str) and len(值)>0 and 值==值.strip()#非空且首尾无空白

def 归一化列表(值):#判断是否为归一化字符串数组
    """判断是否为归一化字符串数组。"""
    return isinstance(值,list) and all(归一化文本(项) for 项 in 值)#每项都是归一化文本

def 读报告(值,期望状态,最大字符):#跨提供方边界防御性解码固定脚本的报告
    """把未知值校成单轮报告。"""
    键集=','.join(sorted(值.keys())) if 是否记录(值) else ''#字段集排序拼接
    if (not 是否记录(值)#不是普通对象
        or 键集!='blocker,evidence,nextSteps,status,summary'#字段集必须恰好这些
        or 取字段(值,'status')!=期望状态#状态必须等于期望
        or not 归一化文本(取字段(值,'summary'))#摘要必须归一化
        or not 归一化列表(取字段(值,'evidence'))#证据必须是归一化列表
        or not 归一化列表(取字段(值,'nextSteps'))#下一步必须是归一化列表
        or not isinstance(取字段(值,'blocker'),str)#阻塞必须是字符串
        or 取字段(值,'blocker')!=取字段(值,'blocker').strip()):#阻塞必须已 trim
        raise 错误('Ralph workflow returned a malformed round report')#报告形态失败
    报告={#组装已校字段
        'status':期望状态,#期望状态
        'summary':取字段(值,'summary'),#摘要
        'evidence':取字段(值,'evidence'),#证据
        'nextSteps':取字段(值,'nextSteps'),#下一步
        'blocker':取字段(值,'blocker'),#阻塞
    }#结束报告对象
    if 期望状态=='continue' and (len(报告['nextSteps'])==0 or 报告['blocker']!=''):#继续态约束
        raise 错误('Ralph workflow returned an invalid continuing report')#继续报告无效
    if 期望状态=='complete' and (len(报告['evidence'])==0 or len(报告['nextSteps'])!=0 or 报告['blocker']!=''):#完成态约束：要有证据、无下一步、空阻塞
        raise 错误('Ralph workflow returned an invalid completion report')#完成报告无效
    if 期望状态=='blocked' and not 归一化文本(报告['blocker']):#阻塞态必须有具体阻塞
        raise 错误('Ralph workflow returned an invalid blocked report')#阻塞报告无效
    字符数=len(json.dumps(报告,ensure_ascii=False,separators=(',',':')))#序列化字符数（紧凑，对齐 JSON.stringify）
    if 字符数>最大字符:#超过交接上限
        raise 错误('Ralph workflow returned an oversized handoff ('+str(字符数)+' > '+str(最大字符)+')')#交接过大
    return 报告#返回已校验报告

def 读运行结果(值,轮数上限,交接上限):#防御性解码固定脚本的终态值
    """把未知值校成终态结果。"""
    已启动=取字段(值,'roundsStarted') if 是否记录(值) else None#已启动轮数
    if (not 是否记录(值)#不是普通对象
        or not isinstance(已启动,(int,float))#轮数不是数字
        or not 是否安全整数(已启动)#不是安全整数
        or 已启动<1#小于 1
        or 已启动>轮数上限):#超过本次上限
        raise 错误('Ralph workflow returned a malformed terminal result')#终态形态失败
    已启动=int(已启动)#规范为 int
    状态=取字段(值,'status')#终态标签
    键集=','.join(sorted(值.keys()))#字段集排序拼接
    if 状态=='complete':#工人报告完成
        if 键集!='report,roundsStarted,status':#字段集必须恰好这些
            raise 错误('Ralph workflow returned a malformed terminal result')#终态形态失败
        return {'status':'complete','roundsStarted':已启动,'report':读报告(取字段(值,'report'),'complete',交接上限)}#解码完成报告
    if 状态=='blocked':#工人报告阻塞
        if 键集!='report,roundsStarted,status':#字段集必须恰好这些
            raise 错误('Ralph workflow returned a malformed terminal result')#终态形态失败
        return {'status':'blocked','roundsStarted':已启动,'report':读报告(取字段(值,'report'),'blocked',交接上限)}#解码阻塞报告
    if 状态=='budget-limited':#打到轮数上限
        if 键集!='report,roundsStarted,status':#字段集必须恰好这些
            raise 错误('Ralph workflow returned a malformed terminal result')#终态形态失败
        if 已启动!=轮数上限:#未打满上限却报预算耗尽
            raise 错误('Ralph workflow returned budget-limited before the round limit')#预算终态与轮数不符
        return {'status':'budget-limited','roundsStarted':已启动,'report':读报告(取字段(值,'report'),'continue',交接上限)}#解码继续态交接
    if 状态=='round-failed':#某轮子运行失败
        if 键集!='lastReport,roundsStarted,status':#字段集必须恰好这些
            raise 错误('Ralph workflow returned a malformed terminal result')#终态形态失败
        上一份=取字段(值,'lastReport')#上一份成功交接
        if 已启动==1:#第一轮就失败
            if 上一份 is not None:#第一轮不得带上一份交接
                raise 错误('Ralph workflow returned an invalid first-round failure')#第一轮失败形态无效
            return {'status':'round-failed','roundsStarted':已启动}#无 lastReport 的第一轮失败
        if 上一份 is None:#后续轮失败却没有上一份交接
            raise 错误('Ralph workflow returned a round failure without its last handoff')#缺少交接
        return {#后续轮失败并带上上一份交接
            'status':'round-failed',#失败标签
            'roundsStarted':已启动,#失败轮次
            'lastReport':读报告(上一份,'continue',交接上限),#解码上一份继续态交接
        }#结束失败结果
    raise 错误('Ralph workflow returned an unknown terminal status')#未知状态

def 停止原因错误(结果):#非干净的工作流结束是错误，绝不是部分 Ralph 成功
    """把停止原因映射为工具错误文案。"""
    原因=取字段(结果,'stopReason')#按停止原因分支
    if 原因=='completed':#干净完成
        return None#不报错
    if 原因=='cancelled':#被取消
        错误=取字段(结果,'error')#可选错误细节
        return 'Ralph workflow was cancelled' if 错误 is None else 'Ralph workflow was cancelled ('+str(错误)+')'#取消文案
    if 原因=='error':#脚本或引擎失败
        错误=取字段(结果,'error')#可选错误细节
        return 'Ralph workflow failed: '+(str(错误) if 错误 is not None else 'unknown error')#失败文案
    return 'Ralph workflow ended abnormally ('+str(原因)+')'#未来新增变体：未知停止原因

def 约束结果(文本,最大字符):#约束面向父方的完整文本，含信封与截断标记
    """按字符上限截断结果文本。"""
    if len(文本)<=最大字符:#未超限则原样
        return 文本#原样
    if 最大字符<=len(截断标记):#上限比标记还短则只留标记前缀
        return 截断标记[:最大字符]#只留标记前缀
    return 文本[:最大字符-len(截断标记)]+截断标记#截断并附标记

def 渲染结果(结果,最大字符):#渲染固定终态信封，不把自我报告当成认证
    """把干净终态渲成模型可见文本。"""
    已启动=取字段(结果,'roundsStarted')#已启动轮数
    轮数=str(已启动)+(' round' if 已启动==1 else ' rounds')#轮数展示
    状态=取字段(结果,'status')#运行状态
    报告文本=json.dumps(取字段(结果,'report'),ensure_ascii=False,indent=2)#美化打印最终报告
    if 状态=='complete':#工人报告完成
        文本='Ralph worker reported completion after '+轮数+'.\nFinal report:\n'+报告文本#完成信封
    elif 状态=='blocked':#工人报告阻塞
        文本='Ralph worker reported a blocker after '+轮数+'.\nFinal report:\n'+报告文本#阻塞信封
    elif 状态=='budget-limited':#打到轮数上限
        文本='Ralph reached its '+轮数+' limit; the worker reported work remaining.\nFinal report:\n'+报告文本#预算耗尽信封
    else:#不应到达：干净终态只有三种
        文本='Ralph worker finished after '+轮数+'.\nFinal report:\n'+报告文本#兜底信封
    return 约束结果(文本,最大字符)#按上限截断

def 渲染轮次失败(结果,最大字符):#用最近一份耐久交接渲染普通子失败
    """把轮次失败渲成错误文本。"""
    头='Ralph round '+str(取字段(结果,'roundsStarted'))+' child failed before producing a structured report.'#失败头
    上一份=取字段(结果,'lastReport')#有没有上一份交接
    if 上一份 is None:#第一轮失败
        文本=头+'\nNo previous handoff was available.'#第一轮失败
    else:#附上上一份交接
        文本=头+'\nLast successful handoff:\n'+json.dumps(上一份,ensure_ascii=False,indent=2)#附上上一份交接
    return 约束结果(文本,最大字符)#按上限截断

def 展示调用(参数):#渲染调用中卡片
    """渲染调用中卡片。"""
    return {'card':'generic','title':'ralph','rawInput':取字段(参数,'objective')}#通用卡片，标题 ralph

def 展示结果(参数,结果):#渲染完成后卡片
    """渲染完成后卡片。"""
    _=参数#展示不依赖参数
    _=结果#展示不依赖结果内容
    return {'card':'generic'}#只声明仍用通用卡片

class 错误(Exception):#对齐上游 throw new Error 文案
    """运行时错误，错误信息保持上游英文原文。"""

def 应用(上下文,配置值=None):#登记固定 Ralph 工具及其显式询问的用法政策
    """登记 Ralph 工具与用法段落。"""
    if 配置值 is None:#缺省配置
        配置值={}#空映射
    已解析=落实配置(配置值)#解析部署配置
    上下文.systemPrompt.section({#登记工具用法段落
        'name':'tool:ralph',#段落名
        'order':116,#段落顺序
        'text':'Use the ralph tool ONLY when the direct human explicitly asks for a Ralph loop or fresh-agent iterative execution. Each Ralph round starts a fresh child with no conversation seed and uses the shared workspace as durable memory. Completion and blockers are worker reports, not independent evaluation. Use same-session goal tools for ordinary long-running objectives, and plain subagents or workflows for bounded delegation and fan-out.',#仅在用户明确要求时使用
    })#结束段落登记

    def 渲染输出(_参数,值):#把结构化结果渲成文本块
        """把结构化结果渲成文本块。"""
        return [{'type':'text','text':渲染结果(取字段(值,'result'),已解析['maxResultChars'])}]#按上限渲染

    def 执行(参数,执行上下文):#执行一次 Ralph 工具调用
        """执行一次 Ralph 工具调用。"""
        父方=取字段(执行上下文,'agent')#取出调用方智能体
        if 父方 is None:#没有调用方智能体
            raise 错误('Ralph tool requires a calling agent (exec.agent was undefined)')#缺少父智能体则失败
        目标=取字段(参数,'objective','').strip()#去掉首尾空白
        if len(目标)==0:#空目标
            raise 错误('Ralph objective must be a non-empty string')#空目标则失败
        轮数上限=落实轮数上限(取字段(参数,'maxRounds'),已解析['maxRounds'])#解析本次轮数上限
        要求全新提供方(上下文,已解析['subagentProvider'])#启动前校验提供方能力
        运行=上下文.workflowEngine.启动({#启动固定 Ralph 工作流
            'script':拉尔夫脚本,#固定编排脚本
            'meta':拉尔夫元数据,#固定身份
            'args':{'objective':目标,'maxRounds':轮数上限,'maxHandoffChars':已解析['maxHandoffChars']},#脚本输入
            'subagentProvider':已解析['subagentProvider'],#全新提供方
            'maxTotalAgents':轮数上限,#子总数等于轮数上限
            'parent':父方,#父智能体
            'signal':取字段(执行上下文,'signal'),#工具取消信号
        })#结束启动请求
        信号=取字段(执行上下文,'signal')#工具取消信号

        def 中止时取消(*_余):#父步骤中止时取消运行
            """父步骤中止时取消运行。"""
            运行.取消('parent step aborted')#取消运行

        if 信号 is not None:#有取消信号
            追加监听=getattr(信号,'addEventListener',None)#浏览器式监听
            if callable(追加监听):#有 addEventListener
                追加监听('abort',中止时取消,{'once':True})#只监听一次中止
            elif hasattr(信号,'aborted'):#已有 aborted 属性
                pass#Python 侧可能用其它桥接
            if 取字段(信号,'aborted'):#已经中止则立即取消
                运行.取消('parent step aborted')#立即取消
        try:#等待运行结算
            已结算=运行.result#等待脚本结算（可能是承诺）
            if hasattr(已结算,'等待'):#可等待
                已结算=已结算.等待()#等待承诺
            错误文案=停止原因错误(已结算)#非干净结束则得到错误文案
            if 错误文案 is not None:#有停止原因错误
                raise 错误(错误文案)#抛出停止原因
            终态=读运行结果(取字段(已结算,'value'),轮数上限,已解析['maxHandoffChars'])#解码终态值
            if 取字段(终态,'status')=='round-failed':#轮次失败
                raise 错误(渲染轮次失败(终态,已解析['maxResultChars']))#轮次失败报成工具错误
            return {#返回结构化成功结果
                'runId':取字段(运行,'id'),#运行标识
                'agentsStarted':取字段(已结算,'agentsStarted'),#智能体计数
                'result':终态,#终态 JSON
            }#结束成功结果
        finally:#无论成败都清理
            if 信号 is not None:#有取消信号
                移除监听=getattr(信号,'removeEventListener',None)#去掉中止桥
                if callable(移除监听):#有 removeEventListener
                    移除监听('abort',中止时取消)#去掉中止桥
            拆除=运行.销毁()#等待脚本与子运行静止
            if hasattr(拆除,'等待'):#可等待
                拆除.等待()#等待拆除完成

    上下文.tools.register(定义工具({#登记面向模型的 Ralph 工具
        'name':'ralph',#工具名
        'description':描述,#工具描述
        'parameters':{#参数模式
            'objective':{#目标参数
                'type':'string',#字符串
                'required':True,#必填
                'description':'The immutable completion objective for every fresh Ralph round.',#目标说明
            },#结束目标参数
            'maxRounds':{#轮数参数
                'type':'number',#数字
                'description':'Optional positive safe-integer round cap, bounded by the deployment ceiling.',#轮数说明
            },#结束轮数参数
        },#结束参数模式
        'output':{#输出模式
            'schema':{#结果 JSON 模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':拉尔夫输出属性,#规范结果字段
            },#结束结果模式
            'render':渲染输出,#把结构化结果渲成文本块
        },#结束输出模式
        'execute':执行,#执行一次 Ralph 工具调用
        'presentCall':展示调用,#调用中展示
        'presentResult':展示结果,#完成后展示
    }))#结束工具登记
    return None#插件 apply 无拆除器（登记经 ctx.effect）

apply=应用#Cordis 插件入口
