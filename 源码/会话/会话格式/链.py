"""纯相邻流式会话格式迁移链。"""
import json#名称重复诊断
from ...工具.值 import 深冻结#深冻结
from .错误 import 会话格式错误,会话格式不支持迁移错误#导入格式错误
from .json import (#从json导入
    快照会话格式头,#快照头
    会话格式计数,#格式计数
    会话格式版本,#版本校验
)#json工具

def 定义会话格式迁移(迁移):#定义迁移
    """校验并冻结一个相邻迁移声明。"""
    名称=迁移['name']#名称
    if not isinstance(名称,str) or len(名称)==0:#名非法
        raise 会话格式错误('Session migration name must be a non-empty string')#错误
    源=会话格式版本(迁移['fromVersion'],名称+' fromVersion')#源版本
    目标=会话格式版本(迁移['toVersion'],名称+' toVersion')#目标版本
    if 目标!=源+1:#非相邻
        raise 会话格式错误(f'{名称} must declare adjacent v{源}->v{源+1}')#错误
    if isinstance(迁移,dict):#映射则冻结副本
        return 深冻结(dict(迁移))#冻结副本
    return 迁移#对象原样

def 创建会话格式链(选项):#创建链
    """编译唯一完整相邻迁移链。"""
    return 已编译会话格式链(选项)#编译实例

class 已编译会话格式链:#已编译链
    """不可变规划器与流式迁移编译器。"""
    def __init__(自身,选项):#构造
        """记下当代版本、有序迁移与当代头恢复器。"""
        自身.当前版本=会话格式版本(选项['currentVersion'],'current Session format version')#当代版本
        自身.恢复当前版本头=选项['restoreCurrentHeader']#恢复头
        按源={}#按源版本索引
        名称集=set()#名称集
        for 候选 in 选项['migrations']:#遍历候选
            迁移=定义会话格式迁移(候选)#定义校验
            源版本=迁移['fromVersion']#源版本
            目标版本=迁移['toVersion']#目标版本
            名称=迁移['name']#名称
            if 源版本 in 按源:#重复源
                raise 会话格式错误(f'Session migration v{源版本}->v{目标版本} is duplicated')#重复
            if 名称 in 名称集:#名重复
                raise 会话格式错误('Session migration name '+json.dumps(名称,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' is duplicated')#名重复
            按源[源版本]=迁移#入索引
            名称集.add(名称)#记名
        有序=[]#有序列表
        for 版本 in range(自身.当前版本):#填满链
            if 版本 not in 按源:#缺失
                raise 会话格式不支持迁移错误(f'Session migration v{版本}->v{版本+1} is missing')#缺失
            迁移=按源[版本]#取迁移
            有序.append(迁移)#追加
        if len(按源)!=len(有序):#有多余
            无效=None#越界源
            for 版本 in 按源.keys():#找越界
                if 版本>=自身.当前版本:#越界
                    无效=版本#记下
                    break#找到
            raise 会话格式错误(f'Session migration from v{无效} does not lead to current v{自身.当前版本}')#错误
        自身.迁移表=tuple(有序)#冻结有序

    def 计划(自身,源版本):#计划
        """返回从一个受支持已存版本起的完整有序计划。"""
        源=会话格式版本(源版本,'stored Session format version')#校验源
        if 源>自身.当前版本:#更新
            raise 会话格式不支持迁移错误(#不支持
                f'stored Session uses newer format v{源}; this build writes v{自身.当前版本}',#消息
            )#错误结束
        return 自身.迁移表[源:]#从源起切片

    def 创建流(自身,源头,源切口,输出):#创建流
        """为一份已解码源产物编译完整迁移阶段链。"""
        头=源头#当前头
        已校验源切口=None if 源切口 is None else 会话格式计数(源切口,'Session inherited event count')#校验源切口
        继承事件数=已校验源切口#继承事件数
        阶段列表=[]#阶段列表
        计划=自身.计划(头['version'])#计划
        for 下标,迁移 in enumerate(计划):#逐步创建
            目标头=自身.推进头(迁移,头)#推进头
            try:#尝试创建阶段
                阶段=迁移['createStage']({#创建
                    'sourceHeader':头,#源头
                    'targetHeader':目标头,#目标头
                    'sourceInheritedEventCount':继承事件数,#源继承数
                    'sourceKind':'decoded' if 下标==0 else 'transformed',#源种类
                })#createStage结束
            except BaseException as 错误:
                抛出不支持拒绝(迁移,错误)#包装拒绝
            头=目标头#推进头
            阶段列表.append({'migration':迁移,'stage':阶段})#追加阶段
            继承事件数=getattr(阶段,'headerInheritedEventCount',None)#推进继承数
        return 已编译会话格式迁移流(#编译流
            头,#头
            已校验源切口,#源切口
            阶段列表,#阶段
            输出,#输出
        )#Compiled结束

    def 迁移头(自身,源):#迁移头
        """仅把受支持头转为当代逻辑表示。"""
        当前=快照会话格式头(源,'stored Session header')#快照头
        for 迁移 in 自身.计划(当前['version']):#逐步迁移
            当前=自身.推进头(迁移,当前)#推进头
        当前=快照会话格式头(自身.恢复当前版本头(当前),'current Session header restoration')#最终恢复
        if 当前['version']!=自身.当前版本:#版本不符
            raise 会话格式错误(#错误
                'current Session header restorer returned v'+str(当前['version'])+'; expected v'+str(自身.当前版本),#消息
            )#Error结束
        return 当前#返回

    def 推进头(自身,迁移,源):#推进头
        """经一相邻边推进头。"""
        名称=迁移['name']#名称
        目标版本=迁移['toVersion']#目标版本
        try:#尝试迁移头
            目标=迁移['migrateHeader'](快照会话格式头(源,名称+' header input'))#迁移
        except BaseException as 错误:
            抛出不支持拒绝(迁移,错误,'Session header')#包装
        当前=快照会话格式头(目标,名称+' header output')#快照输出
        if 当前['version']!=目标版本:#版本不符
            raise 会话格式错误(名称+' header returned v'+str(当前['version'])+'; expected v'+str(目标版本))#错误
        try:#校验目标头
            迁移['validateTargetHeader'](当前)#校验
        except BaseException as 错误:
            抛出不支持拒绝(迁移,错误,'Session header')#包装
        return 当前#返回

class 链式迁移上下文:#链式迁移上下文
    """把一阶段的输出接到下游上下文。"""
    def __init__(自身,条目,输出):#构造
        """记下条目与下游。"""
        自身.条目=条目#条目
        自身.输出=输出#输出

    def emitEvent(自身,事件):#发出事件
        """转换事件并同步发出。"""
        try:#尝试转换
            自身.条目['stage'].transformEvent(事件,自身.输出)#转换事件
        except BaseException as 错误:
            抛出不支持拒绝(自身.条目['migration'],错误)#包装

    def emitRun(自身,游程):#发出游程
        """转换游程并同步发出。"""
        try:#尝试转换
            自身.条目['stage'].transformRun(游程,自身.输出)#转换游程
        except BaseException as 错误:
            抛出不支持拒绝(自身.条目['migration'],错误)#包装

    def finish(自身):#完成
        """完成阶段并返回目标切口。"""
        try:#尝试完成
            目标切口=自身.条目['stage'].finish(自身.输出)#完成阶段
        except BaseException as 错误:
            抛出不支持拒绝(自身.条目['migration'],错误)#包装
        预声明=getattr(自身.条目['stage'],'headerInheritedEventCount',None)#预声明切口
        if 预声明 is not None and 预声明!=目标切口:#变了
            raise 会话格式错误(f'{自身.条目["migration"]["name"]} changed its predeclared inherited cut')#错误
        return 目标切口#返回

class 已编译会话格式迁移流:#已编译迁移流
    """组合迁移链，向其所有者发出已落定当代事件。"""
    def __init__(自身,头,源继承事件数,条目列表,输出):#构造
        """逆序链阶段并记下入口。"""
        自身.header=头#头
        自身.源继承事件数=源继承事件数#源继承数
        阶段数=len(条目列表)#阶段数
        阶段列表=[None]*阶段数#阶段数组
        下游=输出#下游
        for 偏移,条目 in enumerate(reversed(条目列表)):#逆序链
            上下文=链式迁移上下文(条目,下游)#上下文
            阶段列表[阶段数-偏移-1]=上下文#按正序落位
            下游=上下文#上游接下文
        自身.入口=下游#入口
        自身.阶段表=阶段列表#阶段

    def emitEvent(自身,事件):#发出事件
        """委托入口。"""
        自身.入口.emitEvent(事件)#委托入口

    def emitRun(自身,游程):#发出游程
        """委托入口。"""
        自身.入口.emitRun(游程)#委托入口

    def finish(自身):#完成
        """逐步完成并返回当代继承切口。"""
        继承事件数=自身.源继承事件数#继承数
        for 阶段 in 自身.阶段表:#逐步完成
            继承事件数=阶段.finish()#完成
        return 会话格式计数(继承事件数,'finished Session inherited event count')#校验返回

def 抛出不支持拒绝(迁移,错误,主语='Session'):#抛出不支持拒绝
    """把迁移拒绝包装为不支持迁移错误。"""
    if isinstance(错误,会话格式不支持迁移错误):#已是则原样
        raise 错误#原样
    细节=str(错误)#细节
    名称=迁移['name']#名称
    源版本=迁移['fromVersion']#源版本
    raise 会话格式不支持迁移错误(#包装
        f'{名称} refuses this format v{源版本} {主语}: {细节}',#消息
        错误,#原因
    )#Error结束
