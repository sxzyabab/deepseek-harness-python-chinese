import uuid#随机UUID

__all__=['检查器realm会话集']#仅中文公开名

class 检查器realm会话集:#realm会话集
    '为一条 DevTools 连接的每个活动 realm 精确拥有一个后端会话'
    def __init__(自身,realms,客户端源标识=None):#构造
        '打开现有 realm 并订阅变更。指定 Client 时只含 Host 和该源'
        自身.connectionId=str(uuid.uuid4())#连接id
        自身._客户端源标识=客户端源标识#可选 Client 过滤
        自身._realms=realms#注册表
        自身._会话={}#会话表
        自身._监听=set()#监听
        自身._已关闭=False#是否已关闭
        for realm in realms.realms():#打开现有
            if 自身._包含(realm):#在这次连接里
                自身._打开(realm)#打开
        自身._取消订阅=realms.订阅(自身._接收realm)#订阅

    def 全部(自身):#全部会话
        '按注册表的确定性顺序返回活动会话'
        结果=[]#列表
        for realm in 自身._realms.realms():#按注册表顺序
            会话=自身._会话.get(realm.descriptor.realmId)#取会话
            if 会话 is not None:
                结果.append(会话)#收集
        return 结果#返回

    def host(自身):#Host会话
        '返回必需的 Host 会话'
        会话=自身._会话.get(自身._realms.host.descriptor.realmId)#取Host
        if 会话 is None:#不可用
            raise RuntimeError('宿主 Inspector realm 会话不可用')#抛错
        return 会话#返回

    def 按上下文id(自身,contextId):#按上下文id
        '解析一个合成 Client 上下文'
        realm=自身._realms.按上下文id(contextId)#取realm
        return None if realm is None else 自身._会话.get(realm.descriptor.realmId)#取会话

    def 按唯一上下文id(自身,uniqueId):#按唯一上下文
        '解析一个全局唯一的 Client 上下文'
        realm=自身._realms.按唯一上下文id(uniqueId)#取realm
        return None if realm is None else 自身._会话.get(realm.descriptor.realmId)#取会话

    def 按源(自身,源):#按源
        '将一个活动源世代解析到本连接的 realm 会话'
        realm=自身._realms.按源(源)#取realm
        return None if realm is None else 自身._会话.get(realm.descriptor.realmId)#取会话

    def 订阅(自身,监听):#订阅
        '订阅连接本地 realm 会话生命周期'
        自身._监听.add(监听)#加入
        def 拆除():#拆除本监听
            '取消本监听'
            自身._监听.discard(监听)#摘掉
        return 拆除#拆除器

    def 关闭(自身):#关闭
        '关闭全部 realm 会话并停止跟踪注册表'
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身._取消订阅()#取消订阅
        for 会话 in 自身._会话.values():#关全部
            会话['close']()#关闭
        自身._会话.clear()#清空
        自身._监听.clear()#清监听

    def _包含(自身,realm):#是否纳入这次连接
        '未指定 Client 时全要。指定后只要 Host 和该源'
        if 自身._客户端源标识 is None:#不过滤
            return True#全要
        描述=realm.descriptor#描述
        if 描述.kind=='host':#Host 始终在
            return True#要
        return 描述.sourceId==自身._客户端源标识#同一 Client

    def _接收realm(自身,事件):#处理realm事件
        '打开或关闭会话'
        if not 自身._包含(事件['realm']):#不在这次连接里
            return#忽略
        if 事件['type']=='opened':#打开
            会话=自身._打开(事件['realm'])#打开会话
            自身._发出({'type':'opened','session':会话})#发出
            return#返回
        realmId=事件['realm'].descriptor.realmId#realm id
        会话=自身._会话.get(realmId)#取会话
        if 会话 is None:#无
            return#返回
        del 自身._会话[realmId]#删除
        会话['close']()#关闭
        自身._发出({'type':'closed','session':会话})#发出

    def _打开(自身,realm):#打开会话
        '创建并登记会话'
        会话=realm.打开会话()#创建
        自身._会话[realm.descriptor.realmId]=会话#登记
        return 会话#返回

    def _发出(自身,事件):#发出事件
        '隔离投递'
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(事件)#回调
            except Exception:#观察者回调什么都可能抛，收不窄
                pass#一个 CDP 域不能阻止兄弟域观察 realm 生命周期
