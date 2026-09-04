"""从 Cordis 快照到连接中立语义 DOM 的 Worker 投影。

对齐上游 `worker/cdp/domains/dom/model.ts`。公开面仅中文名。
"""
from ...标识 import cdp数字id#后端节点id

__all__=['Cordis_Dom后端']#仅中文公开名

class Cordis_Dom后端:#Cordis DOM后端
    """分配持久后端 id，并投影最新的源快照。"""
    def __init__(自身,trees):#构造
        """订阅树存储并初建文档。"""
        自身._树们=trees#树存储
        自身._键到后端id={}#键到后端id
        自身._监听=set()#监听
        自身._下一后端节点id=1#下一后端id
        自身._下一修订=1#下一修订
        自身._对象到节点={}#对象到节点
        自身._文档=自身._构建()#初建
        自身._取消订阅=trees.订阅(自身._收树)#订阅树

    def 文档(自身):#取文档
        """读取最新的连接中立语义文档。"""
        return 自身._文档#当前

    def 订阅(自身,监听):#订阅
        """订阅完整文档替换与就地 realm 状态变化。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def 关闭(自身):#关闭
        """在 Worker 关闭时释放仓库订阅。"""
        自身._取消订阅()#取消
        自身._监听.clear()#清监听

    def 按对象取节点(自身,源,引用):#按对象取节点
        """将一个源本地对象引用解析为其当前投影节点。"""
        return 自身._对象到节点.get(对象键(源,引用))#查找

    def 按种类取节点(自身,kind,引用):#按种类
        """当 Runtime 路由仅标识 Host 或 Client 所有权时解析引用。"""
        路由=自身._树们.按种类解析对象(kind,引用)#路由
        return None if 路由 is None else 自身.按对象取节点(路由['source'],引用)#节点

    def 按realm取节点(自身,realm,引用):#按realm
        """将一个与 realm 无关的 Runtime 引用解析为其当前投影节点。"""
        if realm.kind=='host':#Host
            return 自身.按种类取节点('host',引用)#Host
        路由=自身._树们.解析对象身份(realm.sourceId,realm.generation,引用)#按身份
        return None if 路由 is None else 自身.按对象取节点(路由['source'],引用)#节点

    def _收树(自身,事件):#收树事件
        """重建文档并差分。"""
        先前=自身._文档#旧文档
        自身._文档=自身._构建()#重建
        if 事件['type']=='source-disconnected':#断开
            自身._发出({'type':'source-disconnected','source':事件['source']})#断开
        变更=文档差分(先前,自身._文档)#差分
        if len(变更)>0:#有变更
            自身._发出({'type':'tree-mutated','mutations':变更})#发出

    def _构建(自身):#构建文档
        """构建不可变文档。"""
        按后端id={}#按id
        父按后端id={}#父
        自身._对象到节点.clear()#清对象索引
        树=自身._树们.树()#检查树
        根=自身._节点('document','#document',[],'#document')#文档根
        Host槽=自身._节点('host','host',[],'<host>')#Host槽
        if 树['host'] is not None:#有Host
            Host槽['children'].append(自身._实体(树['host'],树['host']['snapshot'].root))#Host实体
        Clients槽=自身._节点('clients','clients',[],'<clients>')#Clients槽
        for Client树 in 树['clients']:#扫Client
            Client槽=自身._节点(f"client:{_源字段(Client树['source'],'sourceId')}",'client',[],'<client>')#Client槽
            Client槽['children'].append(自身._实体(Client树,Client树['snapshot'].root))#实体
            Clients槽['children'].append(Client槽)#加入
        根['children'].extend([Host槽,Clients槽])#挂根
        保留键=set()#保留键
        def 冻结(节点,父=None):#冻结
            """递归冻结。"""
            子=[冻结(项,节点) for 项 in 节点['children']]#递归
            值={**节点,'children':子}#冻结节点
            保留键.add(值['key'])#记键
            按后端id[值['backendNodeId']]=值#索引
            if 父 is not None:#有父
                父按后端id[值['backendNodeId']]=父['backendNodeId']#父
            对象=值.get('object')#对象路由
            if 对象 is not None and 对象['connection']['state']=='connected':#已连接
                自身._对象到节点[对象键(对象['source'],{'registryId':对象['snapshot'].objectRegistryId,'handle':对象['node']['objectHandle']})]=值#对象索引
            return 值#返回
        冻结根=冻结(根)#冻结根
        for 键 in list(自身._键到后端id.keys()):#扫键
            if 键 not in 保留键:#废弃
                del 自身._键到后端id[键]#删废弃
        修订=自身._下一修订#修订
        自身._下一修订+=1#推进
        return {'revision':修订,'root':冻结根,'byBackendId':按后端id,'parentByBackendId':父按后端id}#文档

    def _实体(自身,树,节点):#实体节点
        """投影实体节点。"""
        源=树['source']#源
        快照=树['snapshot']#快照
        键=f"entity:{对象键(源,{'registryId':快照.objectRegistryId,'handle':节点['objectHandle']})}"#键
        对象={**树,'node':节点}#对象路由
        属性=[('uid',str(节点['uid']))] if 节点['kind']=='fiber' else []#属性
        投影=自身._节点(键,节点['kind'],属性,元素描述(节点['kind'],属性),对象)#投影
        投影['children'].extend(自身._实体(树,子) for 子 in 节点.get('children',()))#子实体
        return 投影#返回

    def _节点(自身,键,名,属性,描述,对象=None):#创建可变节点
        """创建可变节点。"""
        后端id=自身._键到后端id.get(键)#已有id
        if 后端id is None:#新键
            后端id=cdp数字id(自身._下一后端节点id,'backendNodeId')#分配
            自身._下一后端节点id+=1#推进
            自身._键到后端id[键]=后端id#登记
        节点={'backendNodeId':后端id,'key':键,'name':名,'attributes':list(属性),'description':描述,'children':[]}#节点
        if 对象 is not None:#有对象
            节点['object']=对象#写入
        return 节点#返回

    def _发出(自身,变更):#发出变更
        """隔离回调故障。"""
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(变更)#回调
            except Exception:#故障
                pass#一个已关闭的 CDP 连接不能阻止兄弟会话接收文档变更

def _源字段(源,名):#取源字段
    """支持映射或属性源。"""
    return 源[名] if isinstance(源,dict) else getattr(源,名)#字段

def 元素描述(名,属性):#元素描述
    """标签形描述。"""
    渲染=' '.join(键 if 值=='' else f'{键}={值!r}' for 键,值 in 属性)#属性串
    return f'<{名}>' if 渲染=='' else f'<{名} {渲染}>'#标签形

def 对象键(源,引用):#对象键
    """复合键。"""
    注册表=引用['registryId'] if isinstance(引用,dict) else 引用.registryId#注册表
    句柄=引用['handle'] if isinstance(引用,dict) else 引用.handle#句柄
    return f"{_源字段(源,'sourceId')}\0{_源字段(源,'generation')}\0{注册表}\0{句柄}"#复合键

def 文档差分(先前,当前):#文档差分
    """文档差分。"""
    变更=[]#变更列表
    return 变更 if 节点差分(先前['root'],当前['root'],变更) else [{'type':'document-updated'}]#增量或整更

def 节点差分(先前,当前,变更):#节点差分
    """节点差分。"""
    if 先前['backendNodeId']!=当前['backendNodeId'] or 先前['name']!=当前['name']:#身份变
        return False#需整更
    旧属性=dict(先前['attributes'])#旧属性
    新属性=dict(当前['attributes'])#新属性
    for 名,值 in 新属性.items():#扫新
        if 旧属性.get(名)==值:#未变
            continue#跳过
        变更.append({'type':'attribute-modified','backendNodeId':当前['backendNodeId'],'name':名,'value':值})#修改
    for 名 in 旧属性:#扫旧
        if 名 not in 新属性:#已无
            变更.append({'type':'attribute-removed','backendNodeId':当前['backendNodeId'],'name':名})#移除
    旧id=[子['backendNodeId'] for 子 in 先前['children']]#旧子id
    新id=[子['backendNodeId'] for 子 in 当前['children']]#新子id
    旧集=set(旧id)#旧集
    新集=set(新id)#新集
    保留前=[i for i in 旧id if i in 新集]#保留前序
    保留后=[i for i in 新id if i in 旧集]#保留后序
    if 保留前!=保留后:#顺序变
        变更.append({'type':'children-replaced','parentBackendNodeId':当前['backendNodeId'],'children':list(当前['children'])})#整替换
        return True#可增量
    for 子 in 先前['children']:#扫旧子
        if 子['backendNodeId'] not in 新集:#已移除
            变更.append({'type':'child-removed','parentBackendNodeId':当前['backendNodeId'],'node':子})#移除
    for 索引,子 in enumerate(当前['children']):#扫新子
        if 子['backendNodeId'] in 旧集:#已有
            continue#跳过
        变更.append({'type':'child-inserted','parentBackendNodeId':当前['backendNodeId'],'previousBackendNodeId':0 if 索引==0 else 当前['children'][索引-1]['backendNodeId'],'node':子})#插入
    旧按id={子['backendNodeId']:子 for 子 in 先前['children']}#旧子索引
    for 子 in 当前['children']:#递归
        旧节点=旧按id.get(子['backendNodeId'])#旧节点
        if 旧节点 is not None and not 节点差分(旧节点,子,变更):#失败整更
            return False#失败
    return True#可增量
