from ...存储 import 创建快照存储

__all__=['性能用量策略','默认性能用量']

默认性能用量='detailed'#与设置缺省一致

class 性能用量策略:
    """设置行与聊天统计共用的现场偏好；作用域可写则持久化。"""
    def __init__(自身,宿主):
        """有已接受宿主设置则对齐。"""
        自身.宿主=宿主
        自身.模式=创建快照存储(默认性能用量)
        def 采纳():
            """已接受值写入现场。"""
            快照=宿主.getSnapshot()
            分区=快照['value'] if 'value' in 快照 else None
            if 分区 is not None and 'performanceUsage' in 分区:
                自身.模式.set(分区['performanceUsage'])
        自身.退订=宿主.subscribe(采纳)
        采纳()

    def 拆除(自身):
        """释放已接受值订阅。"""
        自身.退订()

    def 设模式(自身,模式):
        """立即发布选择；作用域支持写入时持久化。"""
        if 模式==自身.模式.getSnapshot():
            return
        自身.模式.set(模式)
        自身.宿主.set('performanceUsage',模式)
