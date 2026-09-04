"""测试拥有的 Remote 面：带显式测试事件驱动器的 $on 订阅。

对齐上游 `client-runtime/src/remote.ts`。公开面仅中文名。
"""
__all__=['测试远程','远程错误']#仅中文公开名

#上游 @deepseek-ai/dsh-typert-protocol RemoteError；包尚未迁完时内联
class 远程错误(Exception):#远程错误
    """Remote 面失败。"""

    def __init__(自身,码,消息,细节=None,cause=None):#构造
        """记下码、消息与细节。"""
        super().__init__(消息)#基类
        自身.code=码#错误码
        自身.message=消息#消息
        自身.details=细节 or {}#细节
        if cause is not None:#有 cause
            自身.__cause__=cause#链式

class 测试远程:#Remote 测试替身
    """转发事件路径的 Remote 服务测试替身。"""

    def __init__(自身,上下文,命名空间们=None):#构造
        """注册为 ctx.remote，并为脚本化命名空间各提供服务。"""
        if 命名空间们 is None:#缺省
            命名空间们={}#空映射
        自身._subscriptions={}#事件订阅表
        自身.$host={'home':None,'isLoopback':True}#Host 事实
        for 名 in 命名空间们:#校验命名空间名
            if 名 in ('emit','$on','$mount','subscriptions','$host') or hasattr(测试远程,名):#会遮蔽
                raise TypeError(f'TestRemote: scripted namespace "{名}" would shadow the double\'s own member')#英文诊断
        for 名,面 in 命名空间们.items():#挂命名空间面
            setattr(自身,名,面)#挂面
        上下文.provide('remote',自身)#提供 remote
        for 名,面 in 命名空间们.items():#提供子面
            上下文.provide(f'remote.{名}',面)#提供子面

    def emit(自身,事件,参数):#投递事件
        """向订阅者投递一次转发的 host 事件。"""
        监听们=自身._subscriptions.get(事件)#取订阅者
        if 监听们 is None:#无订阅
            return#结束
        for 监听 in list(监听们):#派发
            监听(*参数)#调用

    def $on(自身,事件,监听):#订阅
        """订阅一次转发的 host 事件。"""
        监听们=自身._subscriptions.setdefault(事件,set())#取或建集合
        监听们.add(监听)#加入
        def 退订():#退订
            """移除本订阅。"""
            监听们.discard(监听)#退订
        return 退订#退订器

    def $mount(自身):#拒绝挂载
        """生成命名空间挂载，本替身不支持。"""
        raise Error('TestRemote: $mount needs the real Client Remote service')#英文诊断

Error=Exception#错误别名
TestRemote=测试远程#上游名
RemoteError=远程错误#上游名
