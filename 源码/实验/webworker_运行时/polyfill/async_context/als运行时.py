__all__=['创建als运行时']

def 创建als运行时(因果面=None):
    """构建改写后的代码所调用的运行时。

    参数:
        因果面: 来自 `node:async_hooks` 代理的快照面；省略
          则改写惰性（仍跳一个微任务，但不搬状态）。
    返回:
        传给每个模块包装器的运行时对象。
    """
    def 快照():
        """捕获每个实例的当前存储。"""
        if 因果面 is None:
            return None
        return 因果面['snapshot']()

    def 恢复(值):
        """恢复已捕获的快照。"""
        if 因果面 is None:
            return
        因果面['restore'](值)

    def 挂起(值):
        """挂起：拒绝走在令牌内，故令牌始终兑现。"""
        捕获=快照()
        try:
            结果=值() if callable(值) else 值
            return {'ok':True,'value':结果,'snapshot':捕获}
        except BaseException as 错误:
            return {'ok':False,'error':错误,'snapshot':捕获}

    def 恢复令牌(令牌):
        """恢复快照后返回值或重抛错误。"""
        恢复(令牌['snapshot'])
        if 令牌['ok']:
            return 令牌['value'] if 'value' in 令牌 else None
        raise 令牌['error']

    def yield后(捕获,送来):
        """yield 后恢复快照并原样传回消费者送来的值。"""
        恢复(捕获)
        return 送来

    def 迭代器(值):
        """把同步或异步可迭代统一为步进面。"""
        if hasattr(值,'__iter__'):
            内层=iter(值)
            def 下一步(*位置参数):
                """同步步进并包装为 done/value。"""
                try:
                    产出=next(内层,*位置参数) if 位置参数 else next(内层)
                    return {'done':False,'value':产出}
                except StopIteration as 停:
                    return {'done':True,'value':停.value}
            def 关闭(送来=None):
                """关闭同步迭代器。"""
                if hasattr(内层,'close'):
                    内层.close()
                return {'done':True,'value':送来}
            return {'next':下一步,'return':关闭}
        raise TypeError('webworker als: for-await 源不可迭代')

    def 关闭迭代器(迭代):
        """关闭迭代器；关闭失败时忽略。"""
        try:
            if isinstance(迭代,dict) and 'return' in 迭代:
                return 迭代['return'](None)
            if hasattr(迭代,'close'):
                迭代.close()
                return None
            return None
        except Exception:#异步资源.close 可能抛，契约未定所以收不窄
            return None

    return {
        'snapshot':快照,
        'pause':挂起,
        'resume':恢复令牌,
        'afterYield':yield后,
        'iterator':迭代器,
        'close':关闭迭代器,
    }
