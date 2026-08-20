"""挂起宿主交互的载体协议半边。

对齐上游 `runtime/src/client/sessions/pending.ts`。公开面仅中文名。
运行时只掌握信封知识（把 rpcId 回填进 client-response）；领域结果编码归交互的消费方包。
"""

__all__=['挂起交互状态','键前缀','挂起等待']#仅中文公开名

挂起交互状态=('approval','plan-review','question')#侧栏琥珀点状态
键前缀={'approval':'a','question':'q'}#approval→a，question→q

class 挂起等待:#一种挂起等待
    """一次挂起的、由宿主拥有的交互等待：不可变的渲染面加上响应载体。"""

    def __init__(自身,种类,rpc标识,会话标识,载荷,应答):#铸造一次等待
        """由 Session 在收到请求帧时铸造。

        @param 种类 - 交互种类（approval|question）。
        @param rpc标识 - 请求帧的稳定信封 id（保持私有；respond 回显它）。
        @param 会话标识 - 所属会话。
        @param 载荷 - 请求帧的领域字段。
        @param 应答 - client-response 载体（api.respond）。
        """
        自身.种类=种类#判别标签
        自身.键=键前缀[种类]+':'+str(rpc标识)#前缀加 rpcId
        自身.会话标识=会话标识#所属会话
        自身.载荷=载荷#领域字段
        自身._已结清=False#是否已结清
        自身._rpc标识=rpc标识#私有信封 id
        自身._应答=应答#私有载体

    def 应答结果(自身,结果):#发送结果
        """为这次等待发送结果：包进 client-response 信封并回填 rpcId。

        已结清时同步抛出。
        @param 结果 - 结果壳（ok 值 / 错误信封），由调用方做领域编码。
        @returns 载体回执。
        """
        if 自身._已结清:#已结清禁止再发
            raise Exception('pending wait '+自身.键+' is already settled')#同步失败
        return 自身._应答({'type':'client-response','rpcId':自身._rpc标识,'result':结果})#回填后交给载体

    def 标已结清(自身):#标已结清
        """仅 Session 使用的结清标记（权威 resolved 帧已到达）；之后 应答结果() 抛出。"""
        自身._已结清=True#respond 此后同步失败
