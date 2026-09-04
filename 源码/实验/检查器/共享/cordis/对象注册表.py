"""检查器快照所引用活对象的界域本地保留与身份。

对齐上游 `shared/cordis/object-registry.ts`。公开面仅中文名。
"""
import uuid#随机标识
from ..身份 import 检查器id#品牌化

__all__=[#仅中文公开名
    '识别领域对象函数','领域对象注册表','领域对象世代',
    '领域对象表达式','识别领域对象',
]#公开面结束

注册表符号名='dsh.inspector.realm-object-registries'#全局注册表符号名
纤程包装最大深度=8#Fiber then包装最大深度

识别领域对象函数=(#界域对象识别函数源码
    'function () {\n'
    f'  const table = globalThis[Symbol.for({注册表符号名!r})]\n'
    '  if (!(table instanceof Map)) return undefined\n'
    '  for (const registry of table.values()) {\n'
    '    const reference = registry.identify(this)\n'
    '    if (reference !== undefined) return reference\n'
    '  }\n'
    '  return undefined\n'
    '}'
)#函数源码结束

def 注册表们():#取或建全局注册表Map
    """取或建全局注册表 Map。"""
    键='__dsh_inspector_realm_object_registries__'#全局键
    已有=globals().get(键)#已有表
    if isinstance(已有,dict):#复用
        return 已有#复用
    值={}#新建
    globals()[键]=值#挂到模块全局
    return 值#新表

class 领域对象注册表:#界域对象注册表
    """一个界域由其最新语义快照保留的对象有界表。"""
    def __init__(自身):#构造时挂入全局表
        """登记自身。"""
        自身.id=检查器id(str(uuid.uuid4()),'registryId')#注册表标识
        自身.已知={}#对象到句柄（强近似WeakMap）
        自身.保留={}#强引用表
        自身.下一句柄=1#下一句柄序号
        自身.已释放=False#是否已释放
        注册表们()[自身.id]=自身#登记自身

    def 开始(自身):#开启世代
        """开启一次替换世代。"""
        if 自身.已释放:#已释放
            raise Exception('inspector: realm object registry is disposed')#英文诊断
        return 领域对象世代(自身)#新世代

    def 解析(自身,句柄):#按句柄解析
        """解析一个当前不透明句柄。"""
        return 自身.保留.get(句柄)#查强引用表

    def 识别(自身,值):#识别保留对象
        """识别最新快照所保留的一个对象。"""
        if not isinstance(值,(dict,list,type)) and not callable(值) and not isinstance(值,object):#非对象
            if 值 is None:#空
                return None#未识别
        if not isinstance(值,object) or 值 is None:#非对象
            return None#未识别
        候选=值#当前候选
        for 深度 in range(纤程包装最大深度+1):#剥包装
            if 候选 is None:#空
                break#结束
            句柄=自身.已知.get(id(候选))#查已知句柄
            if 句柄 is not None and 自身.保留.get(句柄) is 候选:#命中保留
                return {'registryId':自身.id,'handle':句柄}#线上引用
            try:#探测then包装
                if not hasattr(候选,'__dict__') and not isinstance(候选,dict):#无自有键面
                    return None#非纯then包装
                return None#Python侧不剥then包装
            except Exception:#敌对代理
                return None#放弃本注册表
        return None#未识别

    def 关闭(自身):#关闭注册表
        """从界域移除本注册表并释放全部强引用。"""
        if 自身.已释放:#幂等
            return#已关
        自身.已释放=True#标记释放
        注册表们().pop(自身.id,None)#从全局表删除
        自身.保留.clear()#清空强引用

    def 保留对象(自身,值,下一表):#保留对象
        """在一次待定世代中分配稳定句柄并保留一个值。"""
        句柄=自身.已知.get(id(值))#已有句柄
        if 句柄 is None:#首次见到
            句柄=检查器id(f'object-{自身.下一句柄}','objectHandle')#新句柄
            自身.下一句柄+=1#递增
            自身.已知[id(值)]=句柄#记入弱表近似
        下一表[句柄]=值#写入待定表
        return {'registryId':自身.id,'handle':句柄}#线上引用

    def 提交(自身,下一表):#提交世代
        """用一次完成的世代替换当前强引用集。"""
        自身.保留=下一表#原子替换

class 领域对象世代:#对象世代
    """在快照对消费者可见之前组装的可变对象集。"""
    def __init__(自身,所有者):#所属注册表
        """保存所有者。"""
        自身.所有者=所有者#所属注册表
        自身.保留={}#待定强引用
        自身.已提交=False#是否已提交

    def 保留(自身,值):#保留到本世代
        """保留一个对象并取得其稳定不透明引用。"""
        if 自身.已提交:#已提交
            raise Exception('inspector: realm object generation is already committed')#英文诊断
        return 自身.所有者.保留对象(值,自身.保留)#委托注册表

    def 释放(自身,句柄):#释放句柄
        """停止保留在约束待定快照时被省略的对象。"""
        if 自身.已提交:#已提交
            raise Exception('inspector: realm object generation is already committed')#英文诊断
        自身.保留.pop(句柄,None)#从表删除

    def 提交(自身):#提交本世代
        """原子替换注册表的保留集。"""
        if 自身.已提交:#幂等
            return#已提交
        自身.已提交=True#标记已提交
        自身.所有者.提交(自身.保留)#安装到注册表

def 领域对象表达式(引用):#生成解析表达式
    """构造在其所属界域内解析一条引用的表达式。"""
    return (f'globalThis[Symbol.for({注册表符号名!r})]?.get({引用["registryId"]!r})?'
            f'.resolve({引用["handle"]!r})')#查表解析

def 识别领域对象(值):#跨注册表识别
    """在本界域全部检查器收集器中识别一个保留对象。"""
    for 注册表 in 注册表们().values():#逐注册表
        引用=注册表.识别(值)#尝试识别
        if 引用 is not None:#首个命中
            return 引用#返回
    return None#未命中
