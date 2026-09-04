"""Host/Client 共用的、从活 Cordis 对象到有界语义树的投影。

对齐上游 `shared/cordis/collector.ts`。公开面仅中文名。
"""
from ..json import json字节长度#字节长度
from .快照 import cordis树模式版本#模式版本
from .对象注册表 import 领域对象注册表#对象注册表

__all__=['cordis树上限','cordis树收集器']#仅中文公开名

阴影标记='cordis.shadow'#Cordis阴影标记

class cordis树上限:#树上限
    """快照进入源帧之前施加的边界。"""
    def __init__(自身,maxNodes,maxBytes):#构造
        """保存上限。"""
        自身.maxNodes=maxNodes#最大节点数
        自身.maxBytes=maxBytes#最大编码字节

class cordis树收集器:#树收集器
    """带当前活对象表的界域本地收集器。"""
    def __init__(自身,根,上限):#根与上限
        """保存根与上限并建对象表。"""
        自身.根=根#根Context
        自身.上限=上限#上限
        自身.objects=领域对象注册表()#对象注册表
        自身.修订=0#修订计数

    def 快照(自身):#捕获快照
        """捕获当前可达的 Context/Fiber 树。"""
        收集=收集上下文们(自身.根)#收集可达Context
        树=收集['root']#根信息
        对象们=自身.objects.开始()#开启世代
        状态={'nodeCount':0,'truncated':收集['truncated']}#节点计数与截断

        def 上下文节点(信息):#投影Context
            """投影 Context。"""
            if 状态['nodeCount']>=自身.上限.maxNodes:#触节点上限
                状态['truncated']=True#记截断
                return None#放弃本节点
            状态['nodeCount']+=1#计入
            节点={'kind':'context','objectHandle':对象们.保留(信息['value'])['handle'],'children':[]}#可变Context
            for 子 in 信息['children']:#逐子
                if 子.get('fiber') is not None and getattr(子['fiber'],'ctx',None) is 子['value']:#由Fiber拥有
                    投影=纤程节点(子['fiber'],子)#投影Fiber
                    if 投影 is not None:#入列
                        节点['children'].append(投影)#入列
                else:#普通子Context
                    投影=上下文节点(子)#递归投影
                    if 投影 is not None:#入列
                        节点['children'].append(投影)#入列
            return 节点#Context节点

        def 纤程节点(纤程,拥有):#投影Fiber
            """投影 Fiber。"""
            if getattr(纤程,'uid',None) is None:#无uid则跳过
                return None#跳过
            if 状态['nodeCount']+2>自身.上限.maxNodes:#Fiber+Context会超限
                状态['truncated']=True#记截断
                return None#放弃
            状态['nodeCount']+=1#计入Fiber
            上下文=上下文节点(拥有)#投影拥有的Context
            return {'kind':'fiber','objectHandle':对象们.保留(纤程)['handle'],'uid':纤程.uid,'children':[上下文]}#Fiber

        根节点=上下文节点(树)#投影根
        if 根节点 is None:#根必须留下
            raise Exception('inspector: maxNodes cannot retain the root Context')#英文诊断
        快照={'schemaVersion':cordis树模式版本,'revision':自身.修订+1,'objectRegistryId':自身.objects.id,'root':根节点,'truncated':状态['truncated']}#初稿
        自身.修订+=1#递增修订
        while json字节长度(快照)>自身.上限.maxBytes:#超字节则剪枝
            移除=剪最末(根节点)#剪最末子树
            if len(移除)==0:#无可剪
                break#结束
            for 句柄 in 移除:#释放句柄
                对象们.释放(句柄)#释放
            快照={**快照,'truncated':True}#标记截断
        if json字节长度(快照)>自身.上限.maxBytes:#仍超限
            raise Exception('inspector: Cordis root exceeds the source-frame byte limit')#英文诊断
        对象们.提交()#提交世代
        return 快照#快照

    def 关闭(自身):#关闭收集器
        """释放界域全局解析器与每一个保留对象。"""
        自身.objects.关闭()#关闭注册表

def 收集上下文们(根):#收集可达Context
    """收集可达 Context。"""
    上下文们={}#已见Context
    截断={'v':False}#是否因深度截断

    def 确保(候选,深度=0):#确保入图
        """确保入图。"""
        if 深度>100:#深度保护
            截断['v']=True#记截断
            return None#放弃
        值=去阴影(候选)#去阴影
        if not _是上下文(值):#非Context
            return None#放弃
        已有=上下文们.get(id(值))#已有则复用
        if 已有 is not None:#复用
            return 已有#复用
        if 值 is 根:#根本身
            信息=描述上下文(值)#描述根
            上下文们[id(值)]=信息#入图
            return 信息#根信息
        原型=去阴影(getattr(type(值),'__mro__',[None])[1] if False else getattr(值,'__class__',None))#父近似
        父=确保(getattr(值,'parent',原型),深度+1) if 值 is not 根 else None#确保父
        if 值 is not 根 and 父 is None:#父失败
            信息=描述上下文(值)#仍描述
            上下文们[id(值)]=信息#入图
            return 信息#本信息
        信息=描述上下文(值)#描述本Context
        上下文们[id(值)]=信息#入图
        if 父 is not None:#挂到父
            父['children'].append(信息)#挂到父
        return 信息#本信息

    根信息=确保(根)#确保根
    注册表=getattr(根,'registry',None)#运行时注册表
    if 注册表 is not None:#扫运行时
        for 运行时 in getattr(注册表,'values',lambda: [])():#扫运行时
            for 纤程 in getattr(运行时,'fibers',[]):#扫Fiber
                if getattr(纤程,'uid',None) is None:#无uid跳过
                    continue#跳过
                确保(getattr(纤程,'parent',None))#确保父
                确保(getattr(纤程,'ctx',None))#确保ctx
    return {'root':根信息,'truncated':截断['v']}#收集结果

def 描述上下文(值):#描述单个Context
    """描述单个 Context。"""
    return {'value':值,'children':[],'fiber':getattr(值,'fiber',None)}#初始信息

def 去阴影(值):#剥Cordis阴影包装
    """剥 Cordis 阴影包装。"""
    当前=值#当前值
    while isinstance(当前,dict) and 阴影标记 in 当前:#有阴影标记
        当前=当前.get('__proto__',当前)#上溯近似
        break#Python侧一次
    return 当前#裸值

def _是上下文(值):#是否Context
    """是否 Context。"""
    return 值 is not None and hasattr(值,'registry')#启发式

def 剪最末(上下文):#剪最末叶子并返回释放句柄
    """剪最末叶子并返回释放句柄。"""
    if not 上下文.get('children'):#无子可剪
        return []#空
    子=上下文['children'][-1]#最末子
    if 子.get('kind')=='context':#Context子
        嵌套=剪最末(子)#先剪其内部
        if len(嵌套)>0:#内部有剪
            return 嵌套#返回
        上下文['children'].pop()#去掉该Context
        return [子['objectHandle']]#释放其句柄
    拥有=子['children'][0]#Fiber拥有的Context
    嵌套=剪最末(拥有)#先剪内部
    if len(嵌套)>0:#内部有剪
        return 嵌套#返回
    上下文['children'].pop()#去掉该Fiber
    return [子['objectHandle'],拥有['objectHandle']]#释放Fiber与Context
