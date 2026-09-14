__all__=('收件箱',)#仅中文公开名

class 收件箱:#结构化接口协议
    """Agent 拥有的待处理工作访问面；具体存储归驱动。"""

    @property#下一轮队列
    def 下一轮队列(自身):#等待各自轮次的提示
        """等待各自轮次的提示。"""
        raise NotImplementedError('收件箱.下一轮队列')#由循环实现

    @property#下一步队列
    def 下一步队列(自身):#等待下一个步骤边界的输入
        """等待下一个步骤边界的输入。"""
        raise NotImplementedError('收件箱.下一步队列')#由循环实现

    def 清空(自身):#清空收件箱
        """可持久化取消全部待处理输入，先清下一步再清下一轮。"""
        raise NotImplementedError('收件箱.清空')#由循环实现

    def 追加(自身,目标,消息):#追加消息
        """向待处理列表追加一条消息并持久记录这次插入。"""
        raise NotImplementedError('收件箱.追加')#由循环实现

    def 前置(自身,目标,消息):#前置消息
        """向待处理列表前置一条消息并持久记录这次插入。"""
        raise NotImplementedError('收件箱.前置')#由循环实现

    def 替换(自身,消息身份,新消息):#替换消息
        """原地替换一条待处理消息，身份可以变。"""
        raise NotImplementedError('收件箱.替换')#由循环实现

    def 移除(自身,消息身份):#移除消息
        """移除一条待处理消息并持久记录这次取消。"""
        raise NotImplementedError('收件箱.移除')#由循环实现

    def 拼接(自身,目标,起点,删除数,插入):#公开拼接
        """应用标准拼接语义并持久记录归一化结果。"""
        raise NotImplementedError('收件箱.拼接')#由循环实现
