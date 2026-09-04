"""Worker 拥有的与 CDP 无关的 Cordis 树快照仓库。

对齐上游 `worker/inspection/cordis-store.ts`。公开面仅中文名。
"""
from ...共享.cordis.快照 import 解析cordis树快照#解析快照
from ...共享.桥接.消息.cordis import cordis树主题#树主题
from ...共享.cordis.投影器 import (#投影面
    cordis检查树,cordis树源,cordis树源快照,投影cordis运行时树,
)

__all__=['Cordis树存储']#仅中文公开名

class Cordis树存储:#Cordis树存储
    """经校验的最新值存储，由 CDP 与查询适配器独立消费。"""
    def __init__(自身,选项):#构造
        """保存选项并初始化表。"""
        自身.选项=选项#选项
        自身.topics={cordis树主题}#主题
        自身._树们={}#树表
        自身._断开=set()#断开集合（有序用list模拟插入序）
        自身._断开序=[]#断开顺序
        自身._监听=set()#监听

    def 替换(自身,源,记录们):#替换
        """替换一个源代数的全部保留状态。"""
        下一=自身._最新(源,记录们)#最新快照
        变更=自身._移除(源['sourceId']) if 下一 is None else 自身._安装(源,下一)#移除或安装
        if 变更:#有变更
            自身._发出({'type':'snapshot-changed','source':源})#变更事件

    def 追加(自身,源,记录们):#追加
        """应用后续状态替换，忽略无关观测主题。"""
        下一=自身._最新(源,记录们)#最新
        if 下一 is not None and 自身._安装(源,下一):#变更
            自身._发出({'type':'snapshot-changed','source':源})#变更

    def 关闭(自身,源,原因):#关闭源
        """冻结已关闭源代数的最后一棵树并使其对象路由失效。"""
        当前=自身._树们.get(源['sourceId'])#当前树
        if 当前 is None or 当前['source']['generation']!=源['generation'] or 当前['connection']['state']=='disconnected':#已断或不符
            return#返回
        自身._树们[源['sourceId']]={**当前,'connection':{'state':'disconnected','reason':原因}}#写断开态
        if 源['sourceId'] in 自身._断开:#重排
            自身._断开序.remove(源['sourceId'])#移出序
        自身._断开.add(源['sourceId'])#加入集合
        自身._断开序.append(源['sourceId'])#加入末尾
        while len(自身._断开)>自身.选项['maxDisconnectedTrees']:#超上限
            if not 自身._断开序:#无
                break#中断
            最旧=自身._断开序[0]#最旧
            自身._移除(最旧)#移除
        自身._发出({'type':'source-disconnected','source':源})#断开事件

    def 快照们(自身):#快照列表
        """读取全部当前 realm 快照，不含 CDP 标识。"""
        return [{'source':树['source'],'snapshot':树['snapshot'],'connection':树['connection']} for 树 in 自身._树们.values()]#投影

    def 树(自身):#检查树
        """将公共 realm 模型合成到 Host 与 Client 槽位。"""
        快照列表=自身.快照们()#全部快照
        Host=next((项 for 项 in 快照列表 if _源种类(项['source'])=='host'),None)#Host
        Clients=[项 for 项 in 快照列表 if _源种类(项['source'])=='client']#Clients
        return {'host':Host,'clients':Clients}#合成（完整源描述，供DOM）

    def 读树(自身):#读语义树
        """读取不含对象路由或 CDP 标识的游离语义树。"""
        原始=自身.树()#原始槽位
        return 投影cordis运行时树(cordis检查树(_包装源快照(原始['host']),[_包装源快照(项) for 项 in 原始['clients']]))#投影

    def 解析对象(自身,源,引用):#解析对象
        """将源本地对象引用解析为其语义树节点。"""
        树=自身._树们.get(源['sourceId'])#取树
        if 树 is None or 树['source']['generation']!=源['generation'] or 树['connection']['state']=='disconnected':#不可用
            return None#无
        节点=树['nodesByObject'].get(对象键(引用))#按键取节点
        return None if 节点 is None else 自身._路由(树,节点)#路由

    def 解析对象身份(自身,sourceId,generation,引用):#按身份解析
        """在不需要源展示字段时解析源本地对象。"""
        树=自身._树们.get(sourceId)#取树
        if 树 is None or 树['source']['generation']!=generation or 树['connection']['state']=='disconnected':#不可用
            return None#无
        节点=树['nodesByObject'].get(对象键(引用))#取节点
        return None if 节点 is None else 自身._路由(树,节点)#路由

    def 按种类解析对象(自身,kind,引用):#按种类解析
        """仅知源 realm 种类时解析活动引用。"""
        for 树 in 自身._树们.values():#扫树
            if 树['source']['kind']!=kind or 树['connection']['state']=='disconnected':#跳过
                continue#跳过
            节点=树['nodesByObject'].get(对象键(引用))#取节点
            if 节点 is not None:#命中
                return 自身._路由(树,节点)#路由
        return None#未找到

    def 订阅(自身,监听):#订阅
        """订阅已接受的树替换与源可用性变更。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def _最新(自身,源,记录们):#取最新快照
        """从记录中取最新主题快照。"""
        快照=None#候选
        for 记录 in 记录们:#扫记录
            if 记录.get('topic')!=cordis树主题:#非主题
                continue#跳过
            候选=解析cordis树快照(记录['payload'],自身.选项['maxNodes'])#解析
            if 快照 is None or 候选.revision>快照.revision:#取更新
                快照=候选#候选
        if 快照 is None:#无
            return None#无
        当前=自身._树们.get(源['sourceId'])#当前
        if 当前 is not None and 当前['source']['generation']==源['generation'] and 当前['snapshot'].revision>=快照.revision:#已更新或同
            return 当前['snapshot']#保留当前
        return 快照#返回新

    def _安装(自身,源,快照):#安装快照
        """安装已连接快照。"""
        当前=自身._树们.get(源['sourceId'])#当前
        if 当前 is not None and 当前['source']['generation']==源['generation'] and 当前['snapshot'] is 快照 and 当前['connection']['state']=='connected':#无变更
            return False#无变更
        if 源['sourceId'] in 自身._断开:#移出断开集
            自身._断开.discard(源['sourceId'])#集合
            if 源['sourceId'] in 自身._断开序:#序
                自身._断开序.remove(源['sourceId'])#移除
        索引={}#对象索引
        for 节点 in 展平树节点(快照.root):#展平
            索引[对象键({'registryId':快照.objectRegistryId,'handle':节点['objectHandle']})]=节点#登记
        自身._树们[源['sourceId']]={'source':源,'snapshot':快照,'connection':{'state':'connected'},'nodesByObject':索引}#写入
        return True#已变更

    def _移除(自身,sourceId):#移除树
        """移除树。"""
        自身._断开.discard(sourceId)#断开集
        if sourceId in 自身._断开序:#序
            自身._断开序.remove(sourceId)#移除
        return 自身._树们.pop(sourceId,None) is not None#删除

    def _路由(自身,树,节点):#构造路由
        """构造对象路由。"""
        return {'source':树['source'],'snapshot':树['snapshot'],'connection':树['connection'],'node':节点}#路由对象

    def _发出(自身,事件):#发出事件
        """隔离回调故障。"""
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(事件)#回调
            except Exception:#故障
                pass#一个查询适配器不能阻止后续仓库观察者更新

def _源种类(源):#取源种类
    """支持映射或属性源。"""
    return 源['kind'] if isinstance(源,dict) else 源.kind#种类

def _源字段(源,名):#取源字段
    """支持映射或属性源。"""
    return 源[名] if isinstance(源,dict) else getattr(源,名)#字段

def _包装源快照(项):#包装为投影面
    """把仓库行包装为 cordis树源快照。"""
    if 项 is None:#空
        return None#无
    源=项['source']#源
    源面=cordis树源(_源字段(源,'sourceId'),_源字段(源,'kind'),_源字段(源,'label'))#树源面
    return cordis树源快照(源面,项['snapshot'],项['connection'])#源快照

def 对象键(引用):#对象键
    """注册表+句柄。"""
    注册表=引用['registryId'] if isinstance(引用,dict) else 引用.registryId#注册表
    句柄=引用['handle'] if isinstance(引用,dict) else 引用.handle#句柄
    return f'{注册表}\0{句柄}'#注册表+句柄

def 展平树节点(根):#展平树节点
    """深度优先展平。"""
    节点们=[]#结果
    待定=[根]#栈
    while 待定:#深度优先
        节点=待定.pop()#弹出
        节点们.append(节点)#收集
        子=list(节点.get('children',()))#子节点
        待定.extend(reversed(子))#子节点逆序压栈
    return 节点们#返回
