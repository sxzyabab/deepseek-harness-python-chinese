"""自主目标进入终态后，面向模型的收尾指令。"""
import json#把目标陈述与阻塞原因编进指令

依据说明=(#要求只报告会话已证实的内容
    'Report only what earlier rounds and tool results in this session actually establish; '#字面量不翻译
    + 'when a detail is not in the session, say so instead of inventing it. '#缺则明说
)#依据说明结束
def 渲染收尾上下文(目标陈述,阻塞原因=None):#渲染终态收尾上下文
    """渲染自主目标轮次报告 complete 或 blocked 后注入的收尾消息指令，取代原先的硬停轮，使模型在轮次结束前仍能对用户说一次话。"""
    标题行='Objective: '+json.dumps(目标陈述,ensure_ascii=False)+'\n'#把目标陈述编进标题行
    if 阻塞原因 is None:#无阻塞原因则按完成收尾
        文本=(#完成态收尾指令
            '<goal_complete>\n'#完成开标签
            +标题行#目标陈述
            +'The goal is marked complete and this autonomous run is ending. Write the closing '#字面量不翻译
            +'message to the user now: state the outcome, summarize what was done and how it was '#收尾要求
            +'verified, and point to the concrete results (files, commits, or other artifacts). '#指向具体产物
            +依据说明#只报已证实内容
            +'Note anything the user should review or do next. Address the user directly. Do not '#直接对用户说话
            +"call any more tools in this run; further work waits for the user's next instruction.\n"#本轮不再调工具
            +'</goal_complete>'#完成闭标签
        )#完成文本结束
    else:#有阻塞原因则按阻塞收尾
        文本=(#阻塞态收尾指令
            '<goal_blocked>\n'#阻塞开标签
            +标题行#目标陈述
            +'Blocked: '+json.dumps(阻塞原因,ensure_ascii=False)+'\n'#编进阻塞原因
            +'The goal is marked blocked and this autonomous run is ending. Write the closing '#字面量不翻译
            +'message to the user now: state what has been completed so far, describe the concrete '#说明已完成与阻塞
            +'blocking condition and what you tried, and say exactly what you need from the user to '#明确需要用户做什么
            +'continue. '#继续所需
            +依据说明#只报已证实内容
            +'Address the user directly. Do not call any more tools in this run; further work '#直接对用户说话
            +"waits for the user's next instruction.\n"#本轮不再调工具
            +'</goal_blocked>'#阻塞闭标签
        )#阻塞文本结束
    return [{'type':'text','text':文本}]#包成单块文本内容
