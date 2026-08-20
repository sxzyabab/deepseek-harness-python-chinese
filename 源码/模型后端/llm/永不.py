"""封闭核心联合的穷尽性辅助。

对齐上游 `llm/src/never.ts`。公开面仅中文名；无英文别名。
"""
import json#JSON 渲染

__all__=('断言永不',)#仅中文公开名

def 断言永不(值,现场=None):#封闭联合的不可达分支
    """标记不可达的封闭联合分支，总是抛出。"""
    try:#JSON.stringify 对不可序列化会失败
        渲染=json.dumps(值,ensure_ascii=False)#优先 JSON
    except (TypeError,ValueError):#不可序列化或非法数值
        渲染=None#覆盖不可序列化逃逸
    if 渲染 is None:#JSON 失败
        渲染=str(值)#转字符串
    前缀=''#默认无现场
    if 现场:#有现场标签
        前缀=' in '+现场#前缀进抛出消息
    raise Exception('unreachable variant'+前缀+': '+渲染)#带现场标签抛出
