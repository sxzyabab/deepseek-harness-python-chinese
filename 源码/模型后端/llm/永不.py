'封闭核心联合的穷尽性辅助'
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from .异常 import 永不错误#封闭联合穷尽失败

__all__=('永不错误','断言永不')#仅中文公开名

def 断言永不(值,现场=None):#封闭联合的不可达分支
    '标记不可达的封闭联合分支，总是抛出'
    try:#JSON.stringify 对不可序列化会失败
        渲染=紧凑json编码(值)#优先 JSON
    except (TypeError,ValueError):#不可序列化或非法数值
        渲染=None#覆盖不可序列化逃逸
    if 渲染 is None:#JSON 失败
        渲染=str(值)#转字符串
    前缀=''#默认无现场
    if 现场 is not None and len(现场)>0:#有现场标签
        前缀=' in '+现场#前缀进抛出消息
    raise 永不错误('unreachable variant'+前缀+': '+渲染)#带现场标签抛出
