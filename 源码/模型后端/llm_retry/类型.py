"""会话事件 llm/retry 与 llm/retry-started 的持久载荷说明与字段读取。

对齐上游 `llm-retry/src/types.ts`。公开面仅中文名；无英文别名。

llm/retry 普通模式：retryId,turn,step,provider,mode=normal,
policyKey,retry,maxRetries,delayMs,failure
llm/retry 始终模式：retryId,turn,step,provider,mode=always,
policyKey,retry,delayMs,failure
llm/retry-started：retryId,turn,step,retry
failure 为 llm 的提供方中立失败事实。
"""
from .. import llm#失败事实词表所属包
from .品牌 import 重试身份#再导出重试链身份

__all__=('重试身份','取','有键','试取')#仅中文公开名

def 取(对象,键):#读取必填字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#按下标
    return getattr(对象,键)#按属性

def 有键(对象,键):#对齐 JS 键 in 对象
    """键是否存在；值为 None 仍算有键。"""
    if 对象 is None:#无对象
        return False#无对象
    if isinstance(对象,dict):#映射
        return 键 in 对象#按下标
    return hasattr(对象,键)#按属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if llm.类型.缺席(对象,键):#缺键或值为空
        return None#对齐 undefined
    return 取(对象,键)#已有值
