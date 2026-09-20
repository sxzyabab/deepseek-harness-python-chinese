__all__=['创建合成交换']

def 创建合成交换(帧,汇):
    """为一次隧道请求构建请求/响应对。

    `res.end()` 是落地点：被捕获的监听器返回 void，故由响应对象自身
    报告完成。`write()` 始终返回 true，从而跳过隧道本就无法观察的
    背压等待。

    参数:
        帧: 已校验的请求帧。
        汇: 响应用于发出帧的端。
    返回:
        交给被捕获请求监听器的对。
    """
    监听表={}
    状态=[200]
    头表=[{}]
    流式=[False]
    已结束=[False]
    已中止=[False]

    def 触发(事件):
        """逐个回调某事件的监听器。"""
        if 事件 not in 监听表:
            return
        for 回调 in list(监听表[事件]):
            回调()

    def 销毁请求():
        """标记请求已中止。"""
        已中止[0]=True

    def 请求体迭代():
        """产出请求正文的一块字节。"""
        if 'body' not in 帧:
            return
        正文=帧['body']
        if 正文 is None or len(正文)==0:
            return
        yield bytes(正文)

    请求={
        'url':帧['url'],
        'method':帧['method'],
        'headers':帧['headers'],
        'destroy':销毁请求,
        '__iter__':请求体迭代,
    }

    def 写头(下一状态,下一头=None):
        """记下状态与头并链式返回响应。"""
        状态[0]=下一状态
        if 下一头 is not None:
            头表[0]={}
            for 键,值 in 下一头.items():
                头表[0][键.lower()]=str(值)
        return 响应

    def 写块(块):
        """写一块正文；首次写时发头。"""
        if 已结束[0] or 已中止[0]:
            return False
        if not 流式[0]:
            流式[0]=True
            汇['head'](状态[0],头表[0])
        字节=块.encode('utf-8') if isinstance(块,str) else bytes(块)
        汇['chunk'](字节)
        return True

    def 结束(正文=None):
        """结束响应；一元或流式。"""
        if 已结束[0]:
            return 响应
        已结束[0]=True
        字节=None if 正文 is None else (正文.encode('utf-8') if isinstance(正文,str) else bytes(正文))
        if 流式[0]:
            if 字节 is not None:
                汇['chunk'](字节)
            汇['end']()
        else:
            汇['end']({'status':状态[0],'headers':头表[0],'body':字节})
        触发('close')
        return 响应

    def 销毁响应():
        """报告失败并关闭。"""
        if 已结束[0]:
            return
        已结束[0]=True
        汇['fail'](f'response destroyed for {帧["method"]} {帧["url"]}')
        触发('close')

    def 注册(事件,回调):
        """注册事件监听并链式返回。"""
        if 事件 not in 监听表:
            监听表[事件]=set()
        监听表[事件].add(回调)
        return 响应

    def 移除(事件,回调):
        """移除事件监听并链式返回。"""
        if 事件 in 监听表:
            监听表[事件].discard(回调)
        return 响应

    响应={
        'writeHead':写头,
        'write':写块,
        'end':结束,
        'destroy':销毁响应,
        'on':注册,
        'off':移除,
        'once':注册,#'once'等同on
    }

    def 读中止():
        """页面是否在请求完成前放弃。"""
        return 已中止[0]

    def 中止交换():
        """标记页面已离开：发出 close 并停止后续帧。"""
        if 已结束[0]:
            return
        已中止[0]=True
        已结束[0]=True
        触发('close')

    return {
        'req':请求,
        'res':响应,
        'aborted':读中止,
        'abort':中止交换,
    }
