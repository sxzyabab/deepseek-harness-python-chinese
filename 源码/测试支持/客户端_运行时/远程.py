from ...基础设施.通用工具 import 设置内部数据
from .异常 import 客户端测试运行时错误,远程错误#本包异常
__all__=['测试远程','远程错误']#仅中文公开名

class 测试远程:#Remote 测试替身
    '转发事件路径的 Remote 服务测试替身'

    def __init__(自身,上下文,命名空间表=None):#构造
        '注册为 ctx.remote，并为脚本化命名空间各提供服务'
        if 命名空间表 is None:#缺省
            命名空间表={}#空映射
        自身._ctx=上下文#根上下文
        自身._subscriptions={}#事件订阅表
        设置内部数据(自身,'host',{'home':None,'isLoopback':True})#宿主事实
        设置内部数据(自身,'on',自身.订阅)#订阅
        设置内部数据(自身,'mount',自身.拒绝挂载)#挂载
        自身._校验命名空间(命名空间表)#校验
        上下文.提供服务('remote',自身)#提供 remote
        自身._安装命名空间(命名空间表)#安装子面

    def 提供命名空间(自身,命名空间表):#追加命名空间
        '向本 Remote 服务追加脚本化命名空间面'
        自身._校验命名空间(命名空间表)#校验
        自身._安装命名空间(命名空间表)#安装

    def _校验命名空间(自身,命名空间表):#校验命名空间
        '拒绝会遮蔽替身自有成员的命名空间名'
        for 名 in 命名空间表:#逐名
            if 名 in 自身.__dict__ or hasattr(测试远程,名):#会遮蔽
                raise TypeError(f'TestRemote: scripted namespace "{名}" would shadow the double\'s own member')#英文诊断

    def _安装命名空间(自身,命名空间表):#安装命名空间
        '挂面并提供 remote.<name> 服务'
        for 名,面 in 命名空间表.items():#挂命名空间面
            setattr(自身,名,面)#挂面
            自身._ctx.提供服务(f'remote.{名}',面)#提供子面

    def emit(自身,事件,参数):#投递事件
        '向订阅者投递一次转发的 host 事件'
        监听集合=自身._subscriptions.get(事件)#取订阅者
        if 监听集合 is None:#无订阅
            return
        for 监听 in list(监听集合):#派发
            监听(*参数)#调用

    def 订阅(自身,事件,监听):#订阅
        '订阅一次转发的 host 事件'
        监听集合=自身._subscriptions.setdefault(事件,set())#取或建集合
        监听集合.add(监听)#加入
        def 退订():#退订
            '移除本订阅'
            监听集合.discard(监听)#退订
        return 退订#退订器

    def 拒绝挂载(自身):#拒绝挂载
        '生成命名空间挂载，本替身不支持'
        raise 客户端测试运行时错误('TestRemote: $mount needs the real Client Remote service')#英文诊断
