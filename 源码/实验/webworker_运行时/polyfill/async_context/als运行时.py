"""变换后的模块在每个挂起点调用的运行时。

`pause` 快照每个环境存储并交回一个**始终兑现**的令牌（拒绝走在其内）；
`resume` 把该快照恢复为恢复帧的第一件事，再返回值或重抛错误，
使两条完成路径因果精确。状态本身属于 `node:async_hooks` 代理——
本模块只搬动它。

对齐上游 `webworker-runtime/src/polyfill/async-context/als-runtime.ts`。公开面仅中文名。
"""
__all__=['创建als运行时']#仅中文公开名

def 创建als运行时(因果面=None):#构建运行时
    """构建改写后的代码所调用的运行时。

    参数:
        因果面: 来自 `node:async_hooks` 代理的快照面；省略
          则改写惰性（仍跳一个微任务，但不搬状态）。
    返回:
        传给每个模块包装器的运行时对象。
    """
    def 快照():#拍快照
        """捕获每个实例的当前存储。"""
        return None if 因果面 is None else 因果面['snapshot']() if isinstance(因果面,dict) else 因果面.snapshot()#拍快照

    def 恢复(值):#恢复快照
        """恢复已捕获的快照。"""
        if 因果面 is None:#惰性
            return#不搬状态
        if isinstance(因果面,dict):#字典面
            因果面['restore'](值)#恢复
        else:#对象面
            因果面.restore(值)#恢复

    def 挂起(值):#挂起并快照
        """挂起：拒绝走在令牌内，故令牌始终兑现。"""
        捕获=快照()#捕获
        try:#尝试兑现
            结果=值() if callable(值) else 值#结算值
            return {'ok':True,'value':结果,'snapshot':捕获}#成功令牌
        except BaseException as 错误:#失败包入
            return {'ok':False,'error':错误,'snapshot':捕获}#失败令牌

    def 恢复令牌(令牌):#恢复并结算
        """恢复快照后返回值或重抛错误。"""
        恢复(令牌['snapshot'])#先恢复
        if 令牌['ok']:#成功
            return 令牌.get('value')#返回值
        raise 令牌['error']#重抛

    def yield后(捕获,送来):#yield后恢复
        """yield 后恢复快照并原样传回消费者送来的值。"""
        恢复(捕获)#恢复
        return 送来#原样传回

    def 迭代器(值):#统一异步迭代
        """把同步或异步可迭代统一为步进面。"""
        if hasattr(值,'__aiter__'):#异步可迭代
            return 值.__aiter__()#直接用
        if hasattr(值,'__iter__'):#同步可迭代
            内层=iter(值)#同步迭代器
            def 下一步(*位置参数):#下一步
                """同步步进并包装为 done/value。"""
                try:#尝试步进
                    产出=next(内层,*位置参数) if 位置参数 else next(内层)#同步步进
                    return {'done':False,'value':产出}#未完成
                except StopIteration as 停:#完成
                    return {'done':True,'value':停.value}#完成
            def 关闭(送来=None):#提前关闭
                """关闭同步迭代器。"""
                if hasattr(内层,'close'):#可关闭
                    内层.close()#关闭
                return {'done':True,'value':送来}#默认完成
            return {'next':下一步,'return':关闭}#异步包装
        raise TypeError('webworker als: for-await source is neither async nor sync iterable')#拒绝

    def 关闭迭代器(迭代):#关闭
        """关闭迭代器；关闭失败时忽略。"""
        try:#尝试return
            if isinstance(迭代,dict) and 'return' in 迭代:#字典面
                return 迭代['return'](None)#关闭
            if hasattr(迭代,'aclose'):#异步生成器
                return 迭代.aclose()#关闭
            if hasattr(迭代,'close'):#同步关闭
                迭代.close()#关闭
                return None#无值
            return None#无可释放
        except Exception:#关闭失败
            return None#忽略

    return {#运行时对象
        'snapshot':快照,#导出快照
        'pause':挂起,#挂起
        'resume':恢复令牌,#恢复
        'afterYield':yield后,#yield后
        'iterator':迭代器,#统一迭代
        'close':关闭迭代器,#关闭
    }#返回结束
