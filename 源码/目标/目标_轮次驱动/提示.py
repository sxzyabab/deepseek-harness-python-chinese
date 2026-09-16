"""目标轮次续跑提示渲染。"""
import json#目标陈述入提示

__all__=('渲染目标轮次提示',)#仅中文公开名

def 渲染目标轮次提示(目标,轮次):#渲染一整段轮次指令
    """渲染保留在会话历史上的完整目标轮次指令。"""
    return [{#一块文本
        'type':'text',#文本块
        'text':('<goal_round>\n'
            +'Objective: '+json.dumps(目标['objective'],ensure_ascii=False)+'\n'
            +'Round: '+str(轮次)+'/'+str(目标['maxGoalRounds'])+'\n\n'
            +'Continue working toward the objective in this same session. Treat the current workspace, '
            +'tool results, and durable session state as authoritative; inspect them instead of assuming '
            +'earlier narration is still current. Make concrete progress and verify the result. Before '
            +'claiming completion, gather evidence that the whole objective is achieved, read the current '
            +'goal, and mark it complete. If work remains, leave the goal active for the next round. Follow '
            +'the configured goal-tool policy before reporting a blocker.\n'
            +'</goal_round>'),#模型可见指令
    }]#结束内容
