'已监视变更请求的轮询间隔'
__all__=['下次轮询延迟']

def 下次轮询延迟(结果,失败次数,间隔):
    """选择下一次轮询前的毫秒数。
    结果带 code 时按活跃间隔指数退避，不超过最大退避。
    已合并则停止。已关闭用空闲间隔，以便发现重新打开。
    检查未定或可合并性未知时用活跃间隔，否则用空闲间隔。
    停止时返回 None"""
    if 'code' in 结果:#这一次是失败
        return min(间隔['maxBackoffMs'],间隔['activeIntervalMs']*(2**失败次数))
    if 结果['state']=='merged':#合并后不再轮询
        return None
    if 结果['state']=='closed':#关闭后仍看会不会重开
        return 间隔['idleIntervalMs']
    if 结果['checksRollup']=='pending' or 结果['mergeability']=='unknown':#还在变
        return 间隔['activeIntervalMs']
    return 间隔['idleIntervalMs']#已经安定
