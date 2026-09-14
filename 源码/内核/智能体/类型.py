__all__=('下一轮','下一步','收件箱目标','收件箱拼接字段')#仅中文公开名

下一轮='next-turn'#下一轮待处理列表名
下一步='next-step'#下一步待处理列表名
收件箱目标=(下一轮,下一步)#Agent 拥有的两条有序待处理消息列表

收件箱拼接字段=('target','start','removedCount','inserted','outcome')#agent/inbox/spliced 载荷字段
# target：被改的待处理列表（下一轮|下一步）；start：拼接起点；removedCount：删除条数（纯插入时缺席）；
# inserted：插入的用户消息列表；outcome：取消结果标记，仅公开拼接且有删除时为 'canceled'。
# 实时派发先于投影变更，因此同步观察者可读到拼接前的收件箱以恢复被移除的消息。
