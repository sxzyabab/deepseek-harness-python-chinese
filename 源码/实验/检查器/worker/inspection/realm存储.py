"""Worker 拥有的 Host 与 Client realm 定义注册表。"""
#对齐上游 worker/inspection/realm-store.ts

from ..realms.client import Client检查器realm#Client realm

__all__=['检查器realm注册表']#仅中文公开名

class 检查器realm注册表:#realm注册表
    """当前全部可执行 realm 的权威集合。"""
    def __init__(自身,host,客户端路由,客户端源路由):#构造
        """订阅 Client 目标并打开现有 Client。"""
        自身.host=host#Host realm
        自身._客户端路由=客户端路由#Client Runtime路由
        自身._客户端源路由=客户端源路由#Client源路由
        自身._按源Client={}#按源Client
        自身._监听=set()#监听
        for 目标 in 客户端路由.目标们():#现有目标
            自身._打开Client(目标)#打开
        自身._取消订阅=客户端路由.订阅(自身._接收Client)#订阅

    def realms(自身):#列出realm
        """返回每个连接本地会话集使用的 realm 准入顺序。"""
        return [自身.host,*自身._按源Client.values()]#Host+Clients

    def 按上下文id(自身,contextId):#按上下文id
        """解析一个合成 Client 执行上下文。"""
        for realm in 自身._按源Client.values():#扫Client
            if realm.context.kind=='synthetic' and realm.context.id==contextId:#匹配
                return realm#返回
        return None#未找到

    def 按唯一上下文id(自身,uniqueId):#按唯一id
        """解析一个全局唯一的 Client 执行上下文。"""
        for realm in 自身._按源Client.values():#扫Client
            if realm.context.kind=='synthetic' and realm.context.uniqueId==uniqueId:#匹配
                return realm#返回
        return None#未找到

    def 按源(自身,源):#按源
        """解析一个活动源代数的 realm。"""
        if 源['kind']=='host':#Host
            return 自身.host#返回
        realm=自身._按源Client.get(源['sourceId'])#取Client
        if realm is None:#无
            return None#未找到
        return realm if realm.descriptor.generation==源['generation'] else None#代数匹配

    def 订阅(自身,监听):#订阅
        """订阅 Client realm 准入与移除。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def 关闭(自身):#关闭
        """停止观察 Client 目标并清空注册表监听。"""
        自身._取消订阅()#取消订阅
        自身._按源Client.clear()#清空Client
        自身._监听.clear()#清空监听

    def _接收Client(自身,事件):#处理Client事件
        """打开或关闭 Client realm。"""
        if 事件['type']=='opened':#打开
            realm=自身._打开Client(事件['target'])#打开realm
            自身._发出({'type':'opened','realm':realm})#发出
            return#返回
        realm=自身._按源Client.get(事件['target']['source']['sourceId'])#取realm
        if realm is None or realm.目标 is not 事件['target']:#不符
            return#返回
        del 自身._按源Client[事件['target']['source']['sourceId']]#删除
        自身._发出({'type':'closed','realm':realm})#发出

    def _打开Client(自身,目标):#打开Client
        """创建并登记 Client realm。"""
        realm=Client检查器realm(目标,自身._客户端路由,自身._客户端源路由)#创建
        自身._按源Client[目标['source']['sourceId']]=realm#登记
        return realm#返回

    def _发出(自身,事件):#发出事件
        """隔离投递监听。"""
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(事件)#回调
            except Exception:#故障
                pass#一个 DevTools 连接不能扰乱对兄弟连接的 realm 投递
