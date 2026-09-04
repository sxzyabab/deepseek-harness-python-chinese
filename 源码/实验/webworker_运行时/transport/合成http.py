"""隧道请求的 IncomingMessage/ServerResponse 合成。应用的
`node:http` 代理报告绑定成功并捕获 web 服务器的请求监听器；
隧道把这些对喂给该监听器，使真实路由表、其信任围栏以及每个
处理器原样运行。

合成成员恰好是路由处理器会读取的那些；其余故意缺席，
使新消费者大声失败，而非静默读到桩。

对齐上游 `webworker-runtime/src/transport/synthetic-http.ts`。公开面仅中文名。
"""
__all__=['创建合成交换']#仅中文公开名

def 创建合成交换(帧,汇):#构建合成对
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
    监听们={}#事件监听表 name->set
    状态=[200]#当前状态码（可变盒）
    头们=[{}]#当前响应头
    流式=[False]#是否已开始流式
    已结束=[False]#是否已结束
    已中止=[False]#是否已中止

    def 触发(事件):#触发事件
        """逐个回调某事件的监听器。"""
        for 回调 in list(监听们.get(事件,())):#逐个回调
            回调()#调用

    def 销毁请求():#销毁即中止
        """标记请求已中止。"""
        已中止[0]=True#中止

    def 请求体迭代():#正文迭代
        """产出请求正文的一块字节。"""
        正文=帧.get('body')#正文
        if 正文 is None or len(正文)==0:#无正文
            return#结束
        yield bytes(正文)#产出一块

    请求={#合成请求
        'url':帧['url'],#路径与查询
        'method':帧['method'],#方法
        'headers':帧['headers'],#请求头
        'destroy':销毁请求,#销毁即中止
        '__iter__':请求体迭代,#正文迭代别名
    }#req结束

    def 写头(下一状态,下一头=None):#写头
        """记下状态与头并链式返回响应。"""
        状态[0]=下一状态#记下状态
        if 下一头 is not None:#有头
            头们[0]={}#重置
            for 键,值 in 下一头.items():#逐头
                头们[0][键.lower()]=str(值)#小写键
        return 响应#链式返回

    def 写块(块):#写块
        """写一块正文；首次写时发头。"""
        if 已结束[0] or 已中止[0]:#已结束则拒
            return False#拒绝
        if not 流式[0]:#尚未发头
            流式[0]=True#标记流式
            汇['head'](状态[0],头们[0]) if isinstance(汇,dict) else 汇.head(状态[0],头们[0])#发头
        字节=块.encode('utf-8') if isinstance(块,str) else bytes(块)#编码或原字节
        (汇['chunk'] if isinstance(汇,dict) else 汇.chunk)(字节)#发块
        return True#无背压

    def 结束(正文=None):#结束
        """结束响应；一元或流式。"""
        if 已结束[0]:#幂等
            return 响应#链式
        已结束[0]=True#标记结束
        字节=None if 正文 is None else (正文.encode('utf-8') if isinstance(正文,str) else bytes(正文))#可选正文
        结束面=汇['end'] if isinstance(汇,dict) else 汇.end#结束方法
        块面=汇['chunk'] if isinstance(汇,dict) else 汇.chunk#块方法
        if 流式[0]:#已流式
            if 字节 is not None:#末块
                块面(字节)#发末块
            结束面()#流结束
        else:#一元
            结束面({'status':状态[0],'headers':头们[0],'body':字节})#整帧结束
        触发('close')#通知关闭
        return 响应#链式返回

    def 销毁响应():#销毁响应
        """报告失败并关闭。"""
        if 已结束[0]:#已结束
            return#忽略
        已结束[0]=True#标记结束
        失败面=汇['fail'] if isinstance(汇,dict) else 汇.fail#失败方法
        失败面(f'response destroyed for {帧["method"]} {帧["url"]}')#报告失败
        触发('close')#通知关闭

    def 注册(事件,回调):#注册监听
        """注册事件监听并链式返回。"""
        集合=监听们.get(事件)#取集合
        if 集合 is None:#无集合
            集合=set()#新建
            监听们[事件]=集合#写回
        集合.add(回调)#加入
        return 响应#链式返回

    def 移除(事件,回调):#移除监听
        """移除事件监听并链式返回。"""
        集合=监听们.get(事件)#取集合
        if 集合 is not None:#有集合
            集合.discard(回调)#删除
        return 响应#链式返回

    响应={#合成响应
        'writeHead':写头,#写头
        'write':写块,#写块
        'end':结束,#结束
        'destroy':销毁响应,#销毁
        'on':注册,#注册
        'off':移除,#移除
        'once':注册,#'once'等同on
    }#res结束

    def 读中止():#中止读取器
        """页面是否在请求完成前放弃。"""
        return 已中止[0]#当前标志

    def 中止交换():#中止
        """标记页面已离开：发出 close 并停止后续帧。"""
        if 已结束[0]:#已结束则忽略
            return#忽略
        已中止[0]=True#标记中止
        已结束[0]=True#标记结束
        触发('close')#通知关闭

    return {#交换对象
        'req':请求,#请求
        'res':响应,#响应
        'aborted':读中止,#中止读取器（调用方读属性时调用）
        'abort':中止交换,#中止
    }#返回交换
