'从 Markdown 正文前面拆出 YAML 头，不解析 YAML'
import re

__all__=['拆出前置元数据']

前置元数据正则=re.compile(
    r'^\ufeff?---[ \t]*\r?\n(?:([\s\S]*?)\r?\n)??(?:---|\.\.\.)[ \t]*(?:\r?\n|$)',
)

def 拆出前置元数据(文本):
    '有开头的 --- 才算。没闭合则不是前置元数据'
    匹配=前置元数据正则.match(文本)
    if 匹配 is None:
        return None
    源=匹配.group(1)
    return {'source':'' if 源 is None else 源,'body':文本[匹配.end():]}
