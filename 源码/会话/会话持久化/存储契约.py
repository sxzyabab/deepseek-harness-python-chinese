"""后端共享的存储校验：版本门、追加批物化与连续性（对齐 storage-contract.ts）。"""
import math#安全整数
from ...内核.会话 import 会话格式版本,已知会话事件类型,收养会话事件,快照json值#会话包
from .预备 import 持久化错误#包异常
from .协调器 import (#从协调器再导出错误与文案
    会话格式不支持错误,#格式不支持
    会话持久化损坏错误,#损坏
    会话格式版本拒绝文案,#版本拒绝文案
)#错误面

安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER

def 外来安全整数(值):#外来安全整数
    """外来入口的安全整数校验，排除布尔。"""
    if isinstance(值,bool):#布尔
        return False#拒绝
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#范围
    if isinstance(值,float) and math.isfinite(值) and 值==int(值):#整值浮点
        return abs(值)<=安全整数上限#范围
    return False#其它

def 断言已存标识(标识,元):#断言已存 id
    """拒绝未绑定到请求会话 id 的已存元数据。"""
    if 元['id']!=标识:#不一致
        raise 持久化错误(f'stored session identity mismatch: requested "{标识}", header contains "{元["id"]}"')#拒绝

def 断言版本(元,位置=None):#断言格式版本
    """拒绝本构建无法读取的格式版本头。"""
    if 元['version']==会话格式版本:#当代
        return#放过
    原因=会话格式版本拒绝文案(元['id'],元['version'])#文案
    if 位置 is None:#无位置
        raise 会话格式不支持错误(原因)#拒绝
    raise 会话格式不支持错误(原因+' (raw log: '+str(位置.get('path'))+')',位置)#带路径

def 校验已存事件(元,事件列表,位置=None):#校验已存事件
    """就地校验独占已存事件：收养并拒绝未知必填类型。"""
    for 事件 in 事件列表:#逐条
        类型=事件['type']#类型
        if 类型 not in 已知会话事件类型 and 事件.get('ignorable') is not True:#未知且不可忽略
            原因=f'session "{元["id"]}" contains event type "{类型}" (seq {事件["seq"]}) unknown to this harness and not marked ignorable; refusing to interpret the log — it was likely written by a newer harness'#文案
            if 位置 is None:#无位置
                raise 会话格式不支持错误(原因)#拒绝
            raise 会话格式不支持错误(原因+' (raw log: '+str(位置.get('path'))+')',位置)#带路径
        if 类型=='request/header':#请求头
            数据=事件.get('data')#载荷
            if isinstance(数据,dict) and 数据.get('reason')=='fallback':#遗留 fallback
                原因=f'session "{元["id"]}" contains a request/header event (seq {事件["seq"]}) with the unsupported legacy reason "fallback"; refusing to interpret the log — it was written by a retired pre-release harness'#文案
                if 位置 is None:#无位置
                    raise 会话格式不支持错误(原因)#拒绝
                raise 会话格式不支持错误(原因+' (raw log: '+str(位置.get('path'))+')',位置)#带路径
    try:#收养
        for 下标,事件 in enumerate(事件列表):#就地
            事件列表[下标]=收养会话事件(事件)#收养冻结
    except 会话格式不支持错误:#格式拒绝
        raise#原样
    except BaseException as 错误:#校验失败
        raise 会话持久化损坏错误(f'stored session "{元["id"]}" failed validation: {错误}',错误)#包装
    return 事件列表#返回

def 物化创建头(头):#物化创建头
    """单次遍历校验并深快照传给 create 的头。"""
    快照=快照json值(头)#深快照
    if 快照 is None:#无法序列化
        raise TypeError('session metadata must be losslessly JSON-serializable')#拒绝
    if (not 外来安全整数(快照['createdAt'])) or 快照['createdAt']<0:#非法
        raise TypeError('session metadata createdAt must be a non-negative safe integer')#拒绝
    return 快照#返回

def 物化追加批(事件列表):#物化追加批
    """校验并深快照追加批，使校验值正是持久化值。"""
    批次=快照json值(事件列表)#深快照
    if 批次 is None:#无法序列化
        raise TypeError('session event batch is not losslessly JSON-serializable because it contains non-JSON-serializable data')#拒绝
    return 批次#返回

def 断言连续(标识,事件列表,游标):#断言连续 seq
    """拒绝不能连续续写已存日志的批次。"""
    for 下标,事件 in enumerate(事件列表):#逐条
        if 事件['seq']!=游标+下标:#不连续
            raise 持久化错误(f'append seq mismatch for "{标识}": expected {游标+下标} at index {下标}, got {事件["seq"]}')#拒绝

__all__=[#公开面
    '断言已存标识','断言版本','校验已存事件','物化创建头','物化追加批','断言连续',
]#公开面结束
