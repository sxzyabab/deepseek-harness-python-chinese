"""每个 DevTools 会话上，基于 Cordis 树快照的只读 DOM 投影。

对齐上游 `worker/cdp/domains/dom/session.ts`。公开面仅中文名。
"""
import json#属性序列化
from .......内核.智能体循环.辅助 import 解开#可等待则等待
from .....共享.cordis.对象注册表 import 领域对象表达式#对象表达式
from ...协议 import 响应cdp请求#协议
from ...标识 import cdp数字id,cdp字符串id#CDP id

__all__=['Cordis_Dom会话']#仅中文公开名

只读写拒绝方法=frozenset([#只读写拒绝方法
    'DOM.setAttributeValue','DOM.setAttributesAsText','DOM.setNodeName','DOM.setNodeValue',#写属性
    'DOM.setOuterHTML','DOM.removeNode','DOM.moveTo','DOM.copyTo',#结构写
])#READ_ONLY_METHODS结束

默认文档深度=3#默认文档深度

class Cordis_Dom会话:#Cordis DOM会话
    """连接本地 NodeId、搜索与 RemoteObject 映射的拥有者。"""
    def __init__(自身,传输,后端,运行时):#构造
        """订阅文档并装配映射。"""
        自身.传输=传输#传输
        自身._后端=后端#后端
        自身._运行时=运行时#Runtime
        自身._后端到前端={}#后端→前端
        自身._前端到后端={}#前端→后端
        自身._已送子节点=set()#已送子节点
        自身._对象到节点={}#对象→节点
        自身._组到对象={}#组→对象
        自身._搜索={}#搜索结果
        自身._下一节点id=1#下一节点id
        自身._下一搜索id=1#下一搜索id
        自身._已启用=False#是否启用
        自身._取消订阅=后端.订阅(自身._更新文档)#订阅文档

    def 处理(自身,请求):#处理请求
        """处理一条 DOM 命令。"""
        if not 请求['method'].startswith('DOM.'):#非DOM
            return False#未拥有
        自身._响应(请求,lambda:自身._执行(请求['method'],请求['params']))#响应
        return True#已拥有

    def 释放对象(自身,objectId):#释放对象
        """在其拥有者释放对象之前忘记 Runtime 对象映射。"""
        if not isinstance(objectId,str):#类型
            return#返回
        标识=cdp字符串id(objectId,'objectId')#品牌id
        自身._对象到节点.pop(标识,None)#删映射
        for 集合 in 自身._组到对象.values():#组内删
            集合.discard(标识)#删

    def 绑定对象(自身,objectId,realm,引用,group):#绑定对象
        """将任意 realm 的 Runtime 对象识别为当前某个 Cordis 节点。"""
        节点=自身._后端.按realm取节点(realm,引用)#取节点
        if 节点 is None:#无
            return None#无
        自身._绑定对象id(objectId,节点,group)#绑定
        return 呈现(节点)#呈现

    def 释放对象组(自身,group):#释放对象组
        """忘记某个 Runtime 对象组下保留的全部 DOM 映射。"""
        if not isinstance(group,str):#类型
            return#返回
        for 对象id in list(自身._组到对象.get(group,set())):#扫组
            自身._对象到节点.pop(对象id,None)#删映射
        自身._组到对象.pop(group,None)#删组

    def 关闭(自身):#关闭
        """释放连接拥有的 id 与订阅。"""
        自身._取消订阅()#取消订阅
        自身._重置文档()#重置文档
        自身._搜索.clear()#清搜索

    def _执行(自身,方法,参数):#执行方法
        """按方法分发。"""
        if 方法 in 只读写拒绝方法:#只读
            raise Exception('Cordis DOM projection is read-only')#只读
        if 方法=='DOM.enable':#启用
            自身._已启用=True#置位
            return {}#空
        if 方法=='DOM.disable':#禁用
            自身._已启用=False#清位
            自身._重置文档()#重置
            return {}#空
        if 方法=='DOM.getDocument':#取文档
            自身._已启用=True#启用
            return {'root':自身._序列化(自身._后端.文档()['root'],0,深度参数(参数.get('depth'),默认文档深度),True)}#根
        if 方法=='DOM.requestChildNodes':#请求子节点
            节点=自身._从前端id取(参数.get('nodeId'))#取节点
            深度=深度参数(参数.get('depth'),1)#深度
            自身._已送子节点.add(节点['backendNodeId'])#记已送
            自身.传输.发送({'method':'DOM.setChildNodes','params':{'parentId':数字参数(参数.get('nodeId'),'nodeId'),'nodes':[自身._序列化(子,自身._节点id(节点),深度-1,True) for 子 in 节点['children']]}})#推送子
            return {}#空
        if 方法=='DOM.describeNode':#描述节点
            节点=自身._选节点(参数)#选节点
            return {'node':自身._序列化(节点,自身._父前端id(节点),深度参数(参数.get('depth'),1),False)}#描述
        if 方法=='DOM.getAttributes':#取属性
            return {'attributes':[项 for 对 in 自身._从前端id取(参数.get('nodeId'))['attributes'] for 项 in 对]}#扁平属性
        if 方法=='DOM.getOuterHTML':#取外层HTML
            return {'outerHTML':外层html(自身._选节点(参数))}#HTML
        if 方法=='DOM.pushNodesByBackendIdsToFrontend':#后端id推前端
            if not isinstance(参数.get('backendNodeIds'),list):#类型
                raise Exception('backendNodeIds must be an array')#抛错
            节点ids=[]#结果
            for 值 in 参数['backendNodeIds']:#映射
                if not isinstance(值,int) or isinstance(值,bool) or 值<1:#非法
                    节点ids.append(0)#非法
                    continue#下一项
                节点=自身._后端.文档()['byBackendId'].get(cdp后端节点id(值,'backendNodeId'))#取节点
                if 节点 is None:#无
                    节点ids.append(0)#无
                    continue#下一项
                自身._推节点路径(节点)#推路径
                节点ids.append(自身._节点id(节点))#前端id
            return {'nodeIds':节点ids}#返回
        if 方法=='DOM.resolveNode':#解析节点
            return {'object':自身._解析节点(自身._选节点(参数),可选字符串(参数.get('objectGroup')))}#对象
        if 方法=='DOM.requestNode':#请求节点
            对象id=cdp字符串id(字符串参数(参数.get('objectId'),'objectId'),'objectId')#对象id
            绑定=自身._对象到节点.get(对象id)#绑定
            if 绑定 is None:#无绑定
                raise Exception('RemoteObject is not a current Cordis node')#无绑定
            节点=自身._后端.文档()['byBackendId'].get(绑定['backendNodeId'])#取节点
            if 节点 is None:#无节点
                raise Exception('Cordis node is no longer available')#无节点
            自身._推节点路径(节点)#推路径
            return {'nodeId':自身._节点id(节点)}#节点id
        if 方法=='DOM.performSearch':#执行搜索
            查询=字符串参数(参数.get('query'),'query').lower()#查询
            节点们=[自身._节点id(节点) for 节点 in 自身._后端.文档()['byBackendId'].values() if 节点['name']!='#document' and 查询 in 可搜索(节点)]#过滤
            搜索id=f'cordis-search-{自身._下一搜索id}'#搜索id
            自身._下一搜索id+=1#推进
            自身._搜索[搜索id]=节点们#登记
            return {'searchId':搜索id,'resultCount':len(节点们)}#结果
        if 方法=='DOM.getSearchResults':#取搜索结果
            ids=自身._搜索.get(字符串参数(参数.get('searchId'),'searchId'),[])#结果集
            节点ids=ids[非负整数(参数.get('fromIndex'),'fromIndex'):非负整数(参数.get('toIndex'),'toIndex')]#切片
            for 节点id in 节点ids:#扫id
                后端id=自身._前端到后端.get(节点id)#后端id
                节点=None if 后端id is None else 自身._后端.文档()['byBackendId'].get(后端id)#节点
                if 节点 is not None:#有
                    自身._推节点路径(节点)#推路径
            return {'nodeIds':节点ids}#返回
        if 方法=='DOM.discardSearchResults':#丢弃搜索
            自身._搜索.pop(字符串参数(参数.get('searchId'),'searchId'),None)#删除
            return {}#空
        if 方法=='DOM.setInspectedNode':#设检查节点
            自身._从前端id取(参数.get('nodeId'))#校验存在
            return {}#空
        if 方法 in ('DOM.getBoxModel','DOM.getNodeForLocation'):#盒模型/位置
            raise Exception('Cordis semantic nodes do not have browser layout geometry')#无布局
        raise Exception(f'Method not found: {方法}')#抛错

    def _解析节点(自身,节点,对象组):#解析为对象
        """解析为 Runtime 对象。"""
        路由=节点.get('object')#对象路由
        if 路由 is None:#结构节点
            raise Exception('Structural Cordis node has no live Runtime object')#结构节点
        if 路由['connection']['state']=='disconnected':#已断
            raise Exception('Cordis realm is disconnected')#已断
        表达式=领域对象表达式({'registryId':路由['snapshot'].objectRegistryId,'handle':路由['node']['objectHandle']})#表达式
        远程=解开(自身._运行时.解析对象(路由['source'],表达式,对象组))#求值
        原始id=远程.get('objectId')#原始id
        if not isinstance(原始id,str):#无id
            raise Exception('Cordis object lookup returned no RemoteObjectId')#无id
        对象id=cdp字符串id(原始id,'objectId')#品牌id
        自身._绑定对象id(对象id,节点,对象组)#绑定
        return {**远程,**呈现(节点)}#合并呈现

    def _绑定对象id(自身,objectId,节点,group):#绑定对象id
        """登记对象映射。"""
        源=(节点.get('object') or {}).get('source')#源
        if 源 is None:#结构节点
            raise Exception('Structural Cordis node cannot bind a Runtime object')#结构节点
        自身._对象到节点[objectId]={'backendNodeId':节点['backendNodeId'],'sourceId':_源字段(源,'sourceId'),'generation':_源字段(源,'generation')}#登记
        if group is None:#无组
            return#返回
        集合=自身._组到对象.setdefault(group,set())#组集合
        集合.add(objectId)#加入

    def _选节点(自身,参数):#选择节点
        """按前端/后端/对象 id 选节点。"""
        if 参数.get('nodeId') is not None:#按前端id
            return 自身._从前端id取(参数['nodeId'])#返回
        if 参数.get('backendNodeId') is not None:#按后端id
            标识=cdp后端节点id(参数['backendNodeId'],'backendNodeId')#品牌
            节点=自身._后端.文档()['byBackendId'].get(标识)#查找
            if 节点 is not None:#命中
                return 节点#返回
        if isinstance(参数.get('objectId'),str):#按对象id
            绑定=自身._对象到节点.get(cdp字符串id(参数['objectId'],'objectId'))#绑定
            节点=None if 绑定 is None else 自身._后端.文档()['byBackendId'].get(绑定['backendNodeId'])#取节点
            if 节点 is not None:#命中
                return 节点#返回
        raise Exception('Cordis node is not available')#未找到

    def _从前端id取(自身,值):#从前端id取节点
        """从前端 id 取节点。"""
        后端id=自身._前端到后端.get(cdp节点id(值,'nodeId'))#后端id
        节点=None if 后端id is None else 自身._后端.文档()['byBackendId'].get(后端id)#节点
        if 节点 is None:#不可用
            raise Exception('Cordis NodeId is not available in this document')#不可用
        return 节点#返回

    def _序列化(自身,节点,父id,剩余,投递):#序列化节点
        """序列化 CDP 节点。"""
        节点id=自身._节点id(节点)#前端id
        文档=节点['name']=='#document'#是否文档
        含子=剩余>0#含子
        if 投递 and 含子:#记已送
            自身._已送子节点.add(节点['backendNodeId'])#记已送
        结果={'nodeId':节点id,'backendNodeId':节点['backendNodeId'],'nodeType':9 if 文档 else 1,'nodeName':'#document' if 文档 else 节点['name'].upper(),'localName':'' if 文档 else 节点['name'],'nodeValue':'','childNodeCount':len(节点['children']),'attributes':[项 for 对 in 节点['attributes'] for 项 in 对]}#CDP节点
        if 父id!=0:#有父
            结果['parentId']=父id#父
        if 文档:#文档URL
            结果['documentURL']='dsh://cordis'#URL
            结果['baseURL']='dsh://cordis'#base
        if 含子:#含子
            结果['children']=[自身._序列化(子,节点id,剩余-1,投递) for 子 in 节点['children']]#子
        return 结果#返回

    def _推节点路径(自身,节点):#推节点路径
        """投递尚未发送的祖先层级。"""
        文档=自身._后端.文档()#文档
        链=[]#祖先链
        后端id=文档['parentByBackendId'].get(节点['backendNodeId'])#父后端id
        while 后端id is not None:#向上
            父=文档['byBackendId'].get(后端id)#父节点
            if 父 is None:#断链
                break#中断
            链.insert(0,父)#前插
            后端id=文档['parentByBackendId'].get(父['backendNodeId'])#再上
        for 祖先 in 链:#扫祖先
            if 祖先['backendNodeId'] in 自身._已送子节点:#已送
                continue#跳过
            父id=自身._节点id(祖先)#前端id
            自身._已送子节点.add(祖先['backendNodeId'])#记已送
            自身.传输.发送({'method':'DOM.setChildNodes','params':{'parentId':父id,'nodes':[自身._序列化(子,父id,0,True) for 子 in 祖先['children']]}})#推子

    def _忘记子树(自身,节点):#忘记子树投递
        """忘记子树投递记录。"""
        自身._已送子节点.discard(节点['backendNodeId'])#删已送
        for 子 in 节点['children']:#递归
            自身._忘记子树(子)#递归

    def _节点id(自身,节点):#取或分配前端id
        """取或分配前端 id。"""
        节点id=自身._后端到前端.get(节点['backendNodeId'])#已有
        if 节点id is None:#新
            节点id=cdp数字id(自身._下一节点id,'nodeId')#分配
            自身._下一节点id+=1#推进
            自身._后端到前端[节点['backendNodeId']]=节点id#登记
            自身._前端到后端[节点id]=节点['backendNodeId']#反向
        return 节点id#返回

    def _父前端id(自身,节点):#父前端id
        """父前端 id。"""
        父=自身._后端.文档()['parentByBackendId'].get(节点['backendNodeId'])#父后端
        if 父 is None:#无父
            return 0#无父
        父节点=自身._后端.文档()['byBackendId'].get(父)#父节点
        return 0 if 父节点 is None else 自身._节点id(父节点)#前端id

    def _重置文档(自身):#重置文档状态
        """重置文档状态。"""
        自身._后端到前端.clear()#清映射
        自身._前端到后端.clear()#清反向
        自身._对象到节点.clear()#清对象
        自身._组到对象.clear()#清组
        自身._搜索.clear()#清搜索
        自身._已送子节点.clear()#清已送

    def _更新文档(自身,事件):#更新文档
        """处理文档变更。"""
        if 事件['type']=='source-disconnected':#源断开
            自身._释放源对象(事件['source'])#释对象
            return#返回
        if 自身._已启用:#已启用
            for 变更 in 事件['mutations']:#推变更
                自身._发送变更(变更)#推送
        自身._修剪文档状态()#修剪状态

    def _发送变更(自身,变更):#发送变更
        """按类型投影 CDP 事件。"""
        类型=变更['type']#类型
        if 类型=='document-updated':#整文档
            自身._重置文档()#重置
            自身.传输.发送({'method':'DOM.documentUpdated','params':{}})#通知
            return#返回
        if 类型=='child-inserted':#子插入
            父前端=自身._后端到前端.get(变更['parentBackendNodeId'])#父前端
            if 父前端 is None:#父未知
                return#返回
            前驱=0 if 变更['previousBackendNodeId']==0 else 自身._后端到前端.get(变更['previousBackendNodeId'])#前驱
            if 前驱 is None:#前驱未知
                return#返回
            自身._忘记子树(变更['node'])#忘记子树
            自身.传输.发送({'method':'DOM.childNodeInserted','params':{'parentNodeId':父前端,'previousNodeId':前驱,'node':自身._序列化(变更['node'],父前端,0,True)}})#插入
            return#返回
        if 类型=='child-removed':#子移除
            父前端=自身._后端到前端.get(变更['parentBackendNodeId'])#父
            节点id=自身._后端到前端.get(变更['node']['backendNodeId'])#子
            自身._忘记子树(变更['node'])#忘记
            if 父前端 is None or 节点id is None:#未知
                return#返回
            自身.传输.发送({'method':'DOM.childNodeRemoved','params':{'parentNodeId':父前端,'nodeId':节点id}})#移除
            return#返回
        if 类型=='children-replaced':#子替换
            父前端=自身._后端到前端.get(变更['parentBackendNodeId'])#父
            if 父前端 is None:#未知
                return#返回
            for 子 in 变更['children']:#忘记各子
                自身._忘记子树(子)#忘记
            自身._已送子节点.add(变更['parentBackendNodeId'])#记已送
            自身.传输.发送({'method':'DOM.setChildNodes','params':{'parentId':父前端,'nodes':[自身._序列化(子,父前端,0,True) for 子 in 变更['children']]}})#设子
            return#返回
        if 类型=='attribute-modified':#属性修改
            节点id=自身._后端到前端.get(变更['backendNodeId'])#前端id
            if 节点id is not None:#已知
                自身.传输.发送({'method':'DOM.attributeModified','params':{'nodeId':节点id,'name':变更['name'],'value':变更['value']}})#修改
            return#返回
        if 类型=='attribute-removed':#属性移除
            节点id=自身._后端到前端.get(变更['backendNodeId'])#前端id
            if 节点id is not None:#已知
                自身.传输.发送({'method':'DOM.attributeRemoved','params':{'nodeId':节点id,'name':变更['name']}})#移除
            return#返回

    def _修剪文档状态(自身):#修剪文档状态
        """修剪失效映射。"""
        文档=自身._后端.文档()#文档
        for 后端id,节点id in list(自身._后端到前端.items()):#扫映射
            if 后端id in 文档['byBackendId']:#仍在
                continue#跳过
            del 自身._后端到前端[后端id]#删
            自身._前端到后端.pop(节点id,None)#删反向
        for 后端id in list(自身._已送子节点):#扫已送
            if 后端id not in 文档['byBackendId']:#已无
                自身._已送子节点.discard(后端id)#删
        for 对象id,绑定 in list(自身._对象到节点.items()):#扫对象
            节点=文档['byBackendId'].get(绑定['backendNodeId'])#节点
            源=(节点 or {}).get('object',{}).get('source') if 节点 else None#源
            if 源 is not None and _源字段(源,'sourceId')==绑定['sourceId'] and _源字段(源,'generation')==绑定['generation']:#仍有效
                continue#跳过
            del 自身._对象到节点[对象id]#删
            for 组,集合 in list(自身._组到对象.items()):#扫组
                集合.discard(对象id)#删
                if len(集合)==0:#空组
                    del 自身._组到对象[组]#删组
        for 搜索id,节点ids in list(自身._搜索.items()):#扫搜索
            自身._搜索[搜索id]=[节点id for 节点id in 节点ids if (后端id:=自身._前端到后端.get(节点id)) is not None and 后端id in 文档['byBackendId']]#过滤

    def _释放源对象(自身,源):#释放源对象
        """释放某源代数对象映射。"""
        for 对象id,绑定 in list(自身._对象到节点.items()):#扫对象
            if 绑定['sourceId']!=_源字段(源,'sourceId') or 绑定['generation']!=_源字段(源,'generation'):#不符
                continue#跳过
            del 自身._对象到节点[对象id]#删
            for 组,集合 in list(自身._组到对象.items()):#扫组
                集合.discard(对象id)#删
                if len(集合)==0:#空组
                    del 自身._组到对象[组]#删组

    def _响应(自身,请求,操作):#响应请求
        """委托协议响应。"""
        响应cdp请求(自身.传输,请求,操作)#委托

def _源字段(源,名):#取源字段
    """支持映射或属性源。"""
    return 源[名] if isinstance(源,dict) else getattr(源,名)#字段

def 外层html(节点,缩进=''):#外层HTML
    """外层 HTML。"""
    属性=''.join(f' {名}={json.dumps(值,ensure_ascii=False)}' for 名,值 in 节点['attributes'])#属性串
    if len(节点['children'])==0:#自闭合
        return f'{缩进}<{节点["name"]}{属性} />'#自闭合
    子='\n'.join(外层html(项,缩进+'  ') for 项 in 节点['children'])#子HTML
    return f'{缩进}<{节点["name"]}{属性}>\n{子}\n{缩进}</{节点["name"]}>'#开闭标签

def 可搜索(节点):#可搜索文本
    """可搜索文本。"""
    return f"{节点['name']} {节点['description']} {' '.join(项 for 对 in 节点['attributes'] for 项 in 对)}".lower()#拼接小写

def 数字参数(值,名):#非负整数参数
    """非负整数参数。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<0:#校验
        raise Exception(f'{名} must be a non-negative integer')#抛错
    return 值#返回

def 深度参数(值,缺省):#深度参数
    """深度参数。"""
    if 值 is None:#缺省
        return 缺省#缺省
    if 值==-1:#无限
        return float('inf')#无限
    if not isinstance(值,int) or isinstance(值,bool) or 值<1:#非法
        raise Exception('depth must be -1 or a positive integer')#非法
    return 值#返回

def cdp节点id(值,名):#前端节点id
    """前端节点 id。"""
    if not isinstance(值,int) or isinstance(值,bool):#校验
        raise Exception(f'{名} must be an integer')#校验
    return cdp数字id(值,名)#品牌

def cdp后端节点id(值,名):#后端节点id
    """后端节点 id。"""
    if not isinstance(值,int) or isinstance(值,bool):#校验
        raise Exception(f'{名} must be an integer')#校验
    return cdp数字id(值,名)#品牌

def 非负整数(值,名):#非负整数
    """非负整数。"""
    return 数字参数(值,名)#委托

def 字符串参数(值,名):#字符串参数
    """字符串参数。"""
    if not isinstance(值,str):#校验
        raise Exception(f'{名} must be a string')#校验
    return 值#返回

def 可选字符串(值):#可选字符串
    """可选字符串。"""
    if 值 is None:#缺省
        return None#缺省
    return 字符串参数(值,'objectGroup')#校验

def 呈现(节点):#节点呈现
    """节点呈现。"""
    对象=节点.get('object')#对象
    种类=None if 对象 is None else 对象['node']['kind']#种类
    return {'subtype':'node','className':'Fiber' if 种类=='fiber' else 'Context','description':节点['description']}#呈现
