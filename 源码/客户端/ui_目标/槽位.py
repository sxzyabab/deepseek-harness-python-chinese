
__all__=['无当前目标结果','目标激活快照']#仅中文公开名

无当前目标结果={#没有当前目标时的失败结果
    'ok':False,#失败
    'error':{'code':'no-current-goal','message':'no current goal to mutate'},#无当前目标可改
}#结果结束

# 进程内激活快照：与某一确切目标修订对齐；键均为可选
# id — 确切当前目标 id，创建前或清除后缺席
# revision — 激活边沿的确切修订
# activation — 进程内续跑态；尚无匹配边沿时缺席
目标激活快照=dict#GoalActivationSnapshot 形

# GoalBarInjected = GoalBarActions & {hooks:{goalActivation:可观察}}
# 动词：onEdit / onPause / onResume / onClear
