"""纯相邻整产物会话格式迁移链。"""
import json#名称重复诊断
from ...工具.值 import 深冻结#深冻结
from .错误 import 会话格式错误,会话格式不支持迁移错误#导入格式错误
from .json import (#从json导入
    检查会话格式版本,#检查版本
    快照会话格式产物,#快照产物
    快照会话格式头,#快照头
    会话格式版本,#版本校验
)#json工具

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 定义会话格式迁移(迁移):#定义迁移
    """校验并冻结一个相邻迁移声明。"""
    名称=取字段(迁移,'name')#名称
    if not isinstance(名称,str) or len(名称)==0:#名非法
        raise 会话格式错误('Session migration name must be a non-empty string')#错误
    源=会话格式版本(取字段(迁移,'fromVersion'),f'{名称} fromVersion')#源版本
    目标=会话格式版本(取字段(迁移,'toVersion'),f'{名称} toVersion')#目标版本
    if 目标!=源+1:#非相邻
        raise 会话格式错误(f'{名称} must declare adjacent v{源}->v{源+1}')#错误
    if isinstance(迁移,dict):#映射则冻结副本
        return 深冻结(dict(迁移))#冻结副本
    return 迁移#对象原样

def 创建会话格式链(选项):#创建链
    """编译唯一完整相邻迁移链。"""
    return 已编译会话格式链(选项)#编译实例

class 已编译会话格式链:#已编译链
    """纯相邻规划器与整产物迁移运行器。"""
    def __init__(自身,选项):#构造
        """记下当代版本、有序迁移与当代恢复器。"""
        自身.当代版本=会话格式版本(取字段(选项,'currentVersion'),'current Session format version')#当代版本
        自身.currentVersion=自身.当代版本#上游别名
        自身.恢复当代=取字段(选项,'restoreCurrent')#恢复当代
        自身.恢复当代头=取字段(选项,'restoreCurrentHeader')#恢复头
        按源={}#按源版本索引
        名称集=set()#名称集
        for 候选 in 取字段(选项,'migrations'):#遍历候选
            迁移=定义会话格式迁移(候选)#定义校验
            源版本=取字段(迁移,'fromVersion')#源版本
            目标版本=取字段(迁移,'toVersion')#目标版本
            名称=取字段(迁移,'name')#名称
            if 源版本 in 按源:#重复源
                raise 会话格式错误(f'Session migration v{源版本}->v{目标版本} is duplicated')#重复
            if 名称 in 名称集:#名重复
                raise 会话格式错误(f'Session migration name {json.dumps(名称,ensure_ascii=False)} is duplicated')#名重复
            按源[源版本]=迁移#入索引
            名称集.add(名称)#记名
        有序=[]#有序列表
        for 版本 in range(自身.当代版本):#填满链
            迁移=按源.get(版本)#取迁移
            if 迁移 is None:#缺失
                raise 会话格式不支持迁移错误(f'Session migration v{版本}->v{版本+1} is missing')#缺失
            有序.append(迁移)#追加
        if len(按源)!=len(有序):#有多余
            无效=None#越界源
            for 版本 in 按源.keys():#找越界
                if 版本>=自身.当代版本:#越界
                    无效=版本#记下
                    break#找到
            raise 会话格式错误(f'Session migration from v{无效} does not lead to current v{自身.当代版本}')#错误
        自身.迁移们=tuple(有序)#冻结有序

    def 计划(自身,源版本):#计划
        """返回从一个受支持已存版本起的完整有序计划。"""
        源=会话格式版本(源版本,'stored Session format version')#校验源
        if 源>自身.当代版本:#更新
            raise 会话格式不支持迁移错误(#不支持
                f'stored Session uses newer format v{源}; this build writes v{自身.当代版本}',#消息
            )#错误结束
        return 自身.迁移们[源:]#从源起切片

    def 迁移(自身,源):#迁移产物
        """直接恢复当代输入或在内存中完整迁移旧输入。"""
        已存版本=检查会话格式版本(取字段(源,'header'))#已存版本
        当前=快照会话格式产物(源,f'format v{已存版本} source')#快照源
        if 已存版本==自身.当代版本:#已是当代
            当前=快照会话格式产物(自身.恢复当代(当前),'current Session restoration')#恢复
            自身.断言当代(当前)#断言当代
            return 当前#返回
        for 迁移项 in 自身.计划(已存版本):#逐步迁移
            名称=取字段(迁移项,'name')#名称
            目标版本=取字段(迁移项,'toVersion')#目标版本
            try:#尝试迁移
                已迁移=取字段(迁移项,'migrate')(快照会话格式产物(当前,f'{名称} input'))#迁移
            except BaseException as 错误:#失败
                抛出不支持拒绝(迁移项,错误)#包装拒绝
            当前=快照会话格式产物(已迁移,f'{名称} output')#快照输出
            if 取字段(取字段(当前,'header'),'version')!=目标版本:#版本不符
                raise 会话格式错误(f'{名称} returned v{取字段(取字段(当前,"header"),"version")}; expected v{目标版本}')#错误
            try:#校验目标
                取字段(迁移项,'validateTarget')(当前)#校验
            except BaseException as 错误:#失败
                抛出不支持拒绝(迁移项,错误)#包装拒绝
        当前=快照会话格式产物(自身.恢复当代(当前),'current Session restoration')#最终恢复
        自身.断言当代(当前)#断言当代
        return 当前#返回

    def 迁移头(自身,源):#迁移头
        """仅把受支持头转为当代逻辑表示。"""
        当前=快照会话格式头(源,'stored Session header')#快照头
        for 迁移项 in 自身.计划(取字段(当前,'version')):#逐步迁移
            名称=取字段(迁移项,'name')#名称
            目标版本=取字段(迁移项,'toVersion')#目标版本
            try:#尝试
                已迁移=取字段(迁移项,'migrateHeader')(快照会话格式头(当前,f'{名称} header input'))#迁移头
            except BaseException as 错误:#失败
                抛出不支持拒绝(迁移项,错误,'Session header')#包装
            当前=快照会话格式头(已迁移,f'{名称} header output')#快照输出
            if 取字段(当前,'version')!=目标版本:#版本不符
                raise 会话格式错误(f'{名称} header returned v{取字段(当前,"version")}; expected v{目标版本}')#错误
            try:#校验目标头
                取字段(迁移项,'validateTargetHeader')(当前)#校验
            except BaseException as 错误:#失败
                抛出不支持拒绝(迁移项,错误,'Session header')#包装
        当前=快照会话格式头(自身.恢复当代头(当前),'current Session header restoration')#最终恢复
        if 取字段(当前,'version')!=自身.当代版本:#版本不符
            raise 会话格式错误(#错误
                f'current Session header restorer returned v{取字段(当前,"version")}; expected v{自身.当代版本}',#消息
            )#Error结束
        return 当前#返回

    def 断言当代(自身,产物):#断言当代
        """断言产物头已是当代版本。"""
        if 取字段(取字段(产物,'header'),'version')!=自身.当代版本:#不符
            raise 会话格式错误(#错误
                f'current Session restorer returned v{取字段(取字段(产物,"header"),"version")}; expected v{自身.当代版本}',#消息
            )#Error结束

def 抛出不支持拒绝(迁移,错误,主语='Session'):#抛出不支持拒绝
    """把迁移拒绝包装为不支持迁移错误。"""
    if isinstance(错误,会话格式不支持迁移错误):#已是则原样
        raise 错误#原样
    细节=str(错误)#细节
    名称=取字段(迁移,'name')#名称
    源版本=取字段(迁移,'fromVersion')#源版本
    raise 会话格式不支持迁移错误(#包装
        f'{名称} refuses this format v{源版本} {主语}: {细节}',#消息
        错误,#原因
    )#Error结束
