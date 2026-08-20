"""默认的无执行器、无 UI 智能体主干。

对齐上游 `@deepseek-ai/dsh-agent-spine-demo`。公开面仅中文名。捆绑公共服务、后台作业、可选持久化目标、具体循环、本地技能与 agent-instructions，以及面向模型的 shell/技能消费方。本包不提供默认导出（Loader 解包会丢掉 Config）。
"""
from schemastery import 模式#配置模式
from cordis_plugin_timer import 定时器 as Timer#定时器插件
from llm import LlmRuntime#LLM 运行时——若导出名不同则由装配侧别名
from session import SessionStore#会话存储
from session_title import SessionTitleService#会话标题
from system_prompt import SystemPrompt#系统提示词
from tools import ToolRuntime#工具运行时
from skill import SkillRegistry#技能注册表
import skill_filesystem as SkillFileSystem#本地技能提供方
from agent import AgentRegistry#智能体注册表
from goal import GoalService#目标服务
import goal_round_driver as goalSession#同会话目标驱动器
import tool_goal as toolGoal#面向模型的目标工具
from jobs_local import LocalJobRegistry#进程内作业
from invariants import InvariantRegistry#不变量注册表
import session.不变量 as sessionInvariant#会话不变量
import agent.不变量 as agentInvariant#智能体不变量
import scope.不变量 as scopeInvariant#作用域不变量
import agent_loop.不变量 as agentLoopInvariant#循环不变量
import tool_bash as toolBash#bash 工具
import shell_env as bashEnv#bash 环境
import agent_instructions as workspaceContext#工作区上下文
import tool_skill as toolSkill#技能工具
import tool_jobs as toolJobs#作业工具
from agent_loop import AgentLoop#智能体循环
import llm_retry as llmRetry#LLM 重试
from home_paths import 解析Dsh主目录#主目录解析

__all__=[#仅中文公开名
    '名称','配置','应用',
    '技能配置模式','会话标题配置模式','Bash工具配置模式','作业配置模式','作业工具配置模式','目标配置模式',
    '挑选主干配置',
]#公开面结束

名称='agent-spine-demo'#插件名

示例会话标题配置={#示例标题限制
    'fallbackMaxWords':5,#回退最大词数
    'fallbackMaxBytes':40,#回退最大字节
    'maxTitleBytes':80,#接受标题最大字节
}#示例策略结束

技能配置模式=模式.对象({#技能 schema
    'enabled':模式.布尔().默认(True),#默认启用
    'registry':SkillRegistry.Config if hasattr(SkillRegistry,'Config') else 模式.对象({}),#注册表
    'filesystem':SkillFileSystem.Config if hasattr(SkillFileSystem,'Config') else 模式.对象({}),#本地提供方
    'tool':toolSkill.Config if hasattr(toolSkill,'Config') else 模式.对象({}),#技能工具
})#技能 schema 结束

会话标题配置模式=SessionTitleService.Config if hasattr(SessionTitleService,'Config') else 模式.对象({})#会话标题
Bash工具配置模式=模式.联合([模式.常量(False),toolBash.Config if hasattr(toolBash,'Config') else 模式.对象({})])#bash 或 false
作业配置模式=LocalJobRegistry.Config if hasattr(LocalJobRegistry,'Config') else 模式.对象({})#作业
作业工具配置模式=toolJobs.Config if hasattr(toolJobs,'Config') else 模式.对象({})#作业工具
目标配置模式=模式.对象({#目标 schema
    'domain':GoalService.Config if hasattr(GoalService,'Config') else 模式.对象({}),#域
    'tool':toolGoal.Config if hasattr(toolGoal,'Config') else 模式.对象({}),#工具
})#目标结束

配置=模式.对象({#主干组合包配置——字段原样转发给拥有方
    'agents':模式.数组(模式.对象({})),#预创建智能体列表
    'maxParallelToolCalls':模式.数().步长(1).最小(1),#并行上限
    'includeHarnessIdentity':模式.布尔(),#是否含身份
    'includeRuntimeContext':模式.布尔(),#是否含运行时上下文
    'persona':模式.字符串(),#人设
    'toolOrder':模式.数组(模式.字符串()),#工具顺序
    'tools':ToolRuntime.Config if hasattr(ToolRuntime,'Config') else 模式.对象({}),#工具配置
    'dshHome':模式.字符串(),#主目录
    'sessionTitle':会话标题配置模式,#会话标题
    'workspaceContext':模式.联合([模式.常量(False),workspaceContext.Config if hasattr(workspaceContext,'Config') else 模式.对象({})]).必填(),#必须显式
    'skills':技能配置模式,#技能
    'toolBash':Bash工具配置模式,#bash
    'jobs':作业配置模式,#作业
    'toolJobs':模式.联合([模式.常量(False),作业工具配置模式]),#作业工具或 false
    'invariants':InvariantRegistry.Config if hasattr(InvariantRegistry,'Config') else 模式.对象({}),#不变量
    'goals':模式.联合([模式.常量(False),目标配置模式]),#目标或 false
})#配置结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 挑选主干配置(配置值):#挑出主干字段
    """从应用配置拷贝组合包拥有的字段，不泄漏入口设置。"""
    出={}#只拷贝组合包字段
    for 键 in ('maxParallelToolCalls','includeHarnessIdentity','includeRuntimeContext','persona','toolOrder','tools','dshHome','sessionTitle','skills','toolBash','jobs','toolJobs','invariants','goals'):#可选转发
        值=取字段(配置值,键)#可能缺席
        if 值 is not None:#显式才拷
            出[键]=值#收下
    出['workspaceContext']=取字段(配置值,'workspaceContext')#工作区上下文必填
    return 出#spine 字段

def 应用(上下文,配置值):#安装主干组合
    """加载主干。每个 ctx.plugin 挂载组合包 fiber 的一个子插件。"""
    嵌套主目录=取字段(取字段(取字段(配置值,'skills'),'filesystem'),'dshHome')#嵌套本地技能主目录
    顶层主目录=取字段(配置值,'dshHome')#顶层
    if 顶层主目录 is not None and 嵌套主目录 is not None and 解析Dsh主目录(顶层主目录)!=解析Dsh主目录(嵌套主目录):#冲突
        raise Exception('agent-spine-demo: dshHome and skills.filesystem.dshHome must resolve to the same directory')#拒绝
    主目录=解析Dsh主目录(顶层主目录 if 顶层主目录 is not None else 嵌套主目录)#解析后
    上下文.plugin(Timer)#定时器
    上下文.plugin(LlmRuntime)#LLM
    上下文.plugin(SessionStore)#会话
    上下文.plugin(SessionTitleService,取字段(配置值,'sessionTitle') or 示例会话标题配置)#标题
    提示配置={#系统提示词
        'includeHarnessIdentity':取字段(配置值,'includeHarnessIdentity',True),#默认含身份
        'includeRuntimeContext':取字段(配置值,'includeRuntimeContext',True),#默认含上下文
        'persona':取字段(配置值,'persona') or '',#缺省空人设
    }#提示配置
    if 取字段(配置值,'toolOrder') is not None:#显式顺序
        提示配置['toolOrder']=取字段(配置值,'toolOrder')#转发
    上下文.plugin(SystemPrompt,提示配置)#系统提示词
    上下文.plugin(ToolRuntime,取字段(配置值,'tools') or {})#工具注册表
    技能启用=取字段(取字段(配置值,'skills'),'enabled',True)#技能栈是否启用
    if 技能启用:#挂载技能
        上下文.plugin(SkillRegistry,取字段(取字段(配置值,'skills'),'registry') or {})#注册表
        本地配置=dict(取字段(取字段(配置值,'skills'),'filesystem') or {})#本地提供方
        本地配置['dshHome']=主目录#钉 dshHome
        上下文.plugin(SkillFileSystem,本地配置)#本地技能
    上下文.plugin(AgentRegistry)#智能体注册表
    上下文.plugin(llmRetry)#LLM 重试
    目标=取字段(配置值,'goals')#目标栈
    if 目标 is not None and 目标 is not False:#选择了目标
        上下文.plugin(GoalService,取字段(目标,'domain') or {})#目标域
        上下文.plugin(toolGoal,取字段(目标,'tool') or {})#目标工具
        上下文.plugin(goalSession)#同会话驱动器
    上下文.plugin(LocalJobRegistry,取字段(配置值,'jobs') or {})#进程内作业
    上下文.plugin(InvariantRegistry,取字段(配置值,'invariants') or {})#不变量
    上下文.plugin(sessionInvariant)#会话不变量
    上下文.plugin(agentInvariant)#智能体不变量
    上下文.plugin(scopeInvariant)#作用域不变量
    上下文.plugin(agentLoopInvariant)#循环不变量
    if 取字段(配置值,'toolBash') is not False:#本组合拥有 bash
        上下文.plugin(bashEnv,{'dshHome':主目录})#bash 环境
        上下文.plugin(toolBash,取字段(配置值,'toolBash') or {})#bash 工具
    if 取字段(配置值,'workspaceContext') is not False:#未关闭工作区上下文
        上下文.plugin(workspaceContext,取字段(配置值,'workspaceContext'))#agent-instructions
    if 技能启用:#技能工具
        上下文.plugin(toolSkill,取字段(取字段(配置值,'skills'),'tool') or {})#挂载
    if 取字段(配置值,'toolJobs') is not False:#作业工具
        上下文.plugin(toolJobs,取字段(配置值,'toolJobs') or {})#挂载
    循环配置={'agents':取字段(配置值,'agents') or []}#循环
    if 取字段(配置值,'maxParallelToolCalls') is not None:#显式并行
        循环配置['maxParallelToolCalls']=取字段(配置值,'maxParallelToolCalls')#转发
    上下文.plugin(AgentLoop,循环配置)#智能体循环
