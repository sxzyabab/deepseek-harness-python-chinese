"""格式良好的提供方 API 密钥的唯一定义。

对齐上游 `llm/src/api-key.ts`。公开面仅中文名；无英文别名。
"""
import re#正则

__all__=('合法密钥','规范化密钥')#仅中文公开名

合法密钥=re.compile(r'^[\x21-\x7E]+$')#可打印 ASCII，不含空格

def 规范化密钥(原始):#判定已提供密钥
    """判定一条已提供 API 密钥，先修剪两端空白。"""
    值=原始.strip()#去掉两端空白
    if len(值)==0:#修剪后为空
        return {'ok':False,'reason':'empty'}#修剪后为空
    if not 合法密钥.search(值):#含非法字符
        return {'ok':False,'reason':'illegalCharacters'}#含非法字符
    return {'ok':True,'value':值}#合法密钥
