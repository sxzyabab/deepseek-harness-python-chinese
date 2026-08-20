"""同会话目标轮次面向模型的续跑提示词。"""
import json#回显目标陈述为 JSON 字符串

def 渲染目标轮次提示(目标,轮次):#渲染一轮续跑提示
    """渲染写入会话历史的完整目标轮次指令，供 `Agent.followup()` 使用。"""
    陈述=目标['objective'] if isinstance(目标,dict) else getattr(目标,'objective')#目标陈述
    上限=目标['maxGoalRounds'] if isinstance(目标,dict) else getattr(目标,'maxGoalRounds')#轮次上限
    文本=(#单块文本正文
        '<goal_round>\n'#轮次指令开标签
        +'Objective: '+json.dumps(陈述,ensure_ascii=False)+'\n'#回显目标陈述
        +'Round: '+str(轮次)+'/'+str(上限)+'\n\n'#当前轮次与上限
        +'Continue working toward the objective in this same session. Treat the current workspace, '#同会话继续推进
        +'tool results, and durable session state as authoritative; inspect them instead of assuming '#以工作区与日志为准
        +'earlier narration is still current. Make concrete progress and verify the result. Before '#先核实再声称完成
        +'claiming completion, gather evidence that the whole objective is achieved, read the current '#读当前目标再标完成
        +'goal, and mark it complete. If work remains, leave the goal active for the next round. Follow '#未完成则保持活跃
        +'the configured goal-tool policy before reporting a blocker.\n'#阻塞须遵守工具策略
        +'</goal_round>'#轮次指令闭标签
    )#正文结束
    return [{'type':'text','text':文本}]#单块文本数组
