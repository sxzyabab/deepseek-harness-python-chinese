from ..约定.快照 import 聊天快照,聊天节点存储,聊天位置节点索引,聊天回合导航索引,遗留会话切片#快照
from .回合导航 import 回合导航项#导航
from .回合过程呈现 import 聊天回合过程投影器#过程呈现

__all__=['聊天快照构建器','聊天视图定义','登记聊天会话视图']#仅中文公开名

空键=()#空 key
空列表=()#空列表

def 同引用(左,右):#引用序列相等
    """长度与每项 is。"""
    return len(左)==len(右) and all(甲 is 乙 for 甲,乙 in zip(左,右))#相等

def 有序可见(节点列表):#可见节点排序
    """按锚点再 key。"""
    可见=[节 for 节 in 节点列表 if 节['visibility']=='visible']#可见
    def 锚序(节):#锚点再 key
        """排序键。"""
        return (节['anchorSeq'] if 'anchorSeq' in 节 else 0,节['key'] if 'key' in 节 else '')#键
    return sorted(可见,key=锚序)#排序

class 可变聊天节点存储:#按 key 节点存储
    """get / values / replace / upsert。"""

    def __init__(自身):#空存储
        """key → 节点。"""
        自身.按键={}#表
        自身.值缓存=list(空列表)#缓存
        自身.值脏=False#脏

    def get(自身,键):#按 key 取
        """没有则 None。"""
        return 自身.按键.get(键)#节点

    def values(自身):#全部节点
        """脏则重建。"""
        if 自身.值脏:#脏
            自身.值缓存=list(自身.按键.values())#重建
            自身.值脏=False#对齐
        return 自身.值缓存#列表

    def replace(自身,节点列表):#全量换
        """立刻重建。"""
        自身.按键.clear()#清
        for 节 in 节点列表:#放入
            自身.按键[节['key']]=节#写
        自身.值缓存=list(自身.按键.values())#重建
        自身.值脏=False#对齐

    def upsert(自身,节点列表):#按 key 写入
        """引用相同则跳过。"""
        变了=False#变
        for 节 in 节点列表:#逐个
            键=节['key']#key
            if 自身.按键.get(键) is 节:#同
                continue#跳
            自身.按键[键]=节#换
            变了=True#变
        if 变了:#有
            自身.值脏=True#脏

    def source(自身,键):#按键可观察源
        """稳定源。"""
        def 取快照():#读
            """当前节点。"""
            return 自身.get(键)#节点
        def 订阅(_监听=None):#占位
            """无订阅。"""
            def 退订():#空
                """无。"""
                return None#无
            return 退订#退订
        return {'getSnapshot':取快照,'subscribe':订阅}#源

    def processSource(自身,键):#过程源占位
        """由投影器覆盖。"""
        def 取快照():#空
            """无。"""
            return None#无
        def 订阅(_监听=None):#占位
            """无订阅。"""
            def 退订():#空
                """无。"""
                return None#无
            return 退订#退订
        return {'getSnapshot':取快照,'subscribe':订阅}#空

class 可变聊天位置索引:#位置索引
    """getTurn / getStep / rebuild。"""

    def __init__(自身):#空
        """回合/步骤表。"""
        自身.回合表={}#回合
        自身.步骤表={}#步骤

    def getTurn(自身,回合):#回合键
        """缺席空。"""
        return 自身.回合表.get(回合,空键)#键

    def getStep(自身,回合,步):#步骤键
        """缺席空。"""
        return 自身.步骤表.get(str(回合)+':'+str(步),空键)#键

    def rebuild(自身,序,节点存储):#按可见序重建
        """可沿用旧引用。"""
        回合表={}#可变
        步骤表={}#可变
        for 键 in 序:#按序
            节=节点存储.get(键)#节点
            位置=节['location'] if 节 is not None and 'location' in 节 else None#位置
            种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#种
            if 种=='step':#步骤
                回合位=位置['turn'] if 'turn' in 位置 else None#回合位
                步位=位置['step'] if 'step' in 位置 else None#步位
                回合号=回合位['turn'] if 回合位 is not None and 'turn' in 回合位 else None#回合
                步号=步位['step'] if 步位 is not None and 'step' in 步位 else None#步
                if 回合号 is not None:#有
                    回合表.setdefault(回合号,[]).append(键)#回合
                    步骤表.setdefault(str(回合号)+':'+str(步号),[]).append(键)#步骤
            elif 种=='turn':#回合
                回合位=位置['turn'] if 'turn' in 位置 else None#回合位
                回合号=回合位['turn'] if 回合位 is not None and 'turn' in 回合位 else None#回合
                if 回合号 is not None:#有
                    回合表.setdefault(回合号,[]).append(键)#回合
        自身.回合表={甲:tuple(乙) for 甲,乙 in 回合表.items()}#冻
        自身.步骤表={甲:tuple(乙) for 甲,乙 in 步骤表.items()}#冻

class 聊天快照构建器:#增量快照构建器
    """replace / apply / snapshot。"""

    def __init__(自身):#构造
        """空存储与索引。"""
        自身.节点存储=可变聊天节点存储()#节点存储
        自身.位置=可变聊天位置索引()#位置
        自身.顺序=空键#顺序
        自身.导航项=[]#导航
        自身.过程投影=聊天回合过程投影器()#过程
        自身.时间线={'turnOrder':空列表,'turns':{}}#时间线
        自身.遗留=遗留会话切片(空列表,{},{},None,空列表)#遗留

    def snapshot(自身):#读当前快照
        """ChatSnapshot。"""
        def 过程源(键):#过程源
            """按节点取呈现。"""
            节=自身.节点存储.get(键)#节点
            def 取快照():#读呈现
                """当前呈现。"""
                return 自身.过程投影.get(节)#呈现
            def 订阅(_监听=None):#占位
                """无订阅。"""
                def 退订():#空
                    """无。"""
                    return None#无
                return 退订#退订
            return {'getSnapshot':取快照,'subscribe':订阅}#源
        def 取导航项列表():#当前导航
            """稳定项列表。"""
            return tuple(自身.导航项)#项
        节点面=聊天节点存储(自身.节点存储.get,自身.节点存储.source,过程源,自身.节点存储.values)#存储
        return 聊天快照(#快照
            自身.顺序,#顺序
            节点面,#节点
            自身.位置,#位置
            聊天回合导航索引(取导航项列表),#导航
            自身.时间线,#时间线
            自身.遗留,#遗留
        )#结束

    def replace(自身,节点列表,时间线=None):#全量替换
        """重建顺序、位置、导航、过程。"""
        可见=有序可见(节点列表)#可见
        自身.节点存储.replace(节点列表)#存储
        自身.顺序=tuple(节['key'] for 节 in 可见)#顺序
        自身.位置.rebuild(自身.顺序,自身.节点存储)#位置
        if 时间线 is not None:#有
            自身.时间线=时间线#写
        导航=[]#项
        回合序=自身.时间线['turnOrder'] if 'turnOrder' in 自身.时间线 else []#回合序
        for 回合 in 回合序:#逐轮
            项=回合导航项(回合,自身.位置,自身.节点存储)#投影
            if 项 is not None:#有
                导航.append(项)#收
        自身.导航项=导航#写
        自身.过程投影.replace(自身.顺序,自身.位置,自身.节点存储)#过程
        return 自身.snapshot()#快照

聊天视图定义={#Chat 视图目标定义
    'target':'chat',#目标
}#骨架

def 聊天视图构建(_上下文,节点列表,时间线=None):#构建快照
    """用构建器全量替换。"""
    器=聊天快照构建器()#器
    return 器.replace(节点列表 if 节点列表 is not None else [],时间线)#快照

聊天视图定义['build']=聊天视图构建#挂

def 登记聊天会话视图(上下文):#登记 Chat 视图构造
    """挂到 uiConversation.views。"""
    上下文.uiConversation.views.register(聊天视图定义)#登记
