"""浏览器安全的 `@file` 词法，终端与 Web 客户端共享。

对齐上游 `file-reference/src/grammar.ts`。
"""
import re#正则
from .类型 import 文件引用候选字段#候选字段约定

__all__=['光标处活动令牌','格式化文件提及']#仅中文公开名

_引号令牌=re.compile(r'(?:^|\s)(@"([^"]*))$',re.UNICODE)#引号路径令牌
_普通令牌=re.compile(r'(?:^|\s)(@([^\s]*))$',re.UNICODE)#普通路径令牌

def 光标处活动令牌(行,光标列):#提取光标处的 @ 令牌
    """提取光标处的 @path 或 @\"path\" 令牌；邮箱里的 @ 不算。"""
    光标前=行[:光标列]#光标左侧文本
    引号匹配=_引号令牌.search(光标前)#尝试引号形式
    if 引号匹配 is not None:#命中引号
        return {'prefix':引号匹配.group(1),'query':引号匹配.group(2),'quoted':True}#完整前缀与查询
    普通匹配=_普通令牌.search(光标前)#尝试普通形式
    if 普通匹配 is None:#不在 @ 令牌内
        return None#无活动令牌
    return {'prefix':普通匹配.group(1),'query':普通匹配.group(2),'quoted':False}#普通令牌

def 格式化文件提及(候选,保留引号):#把选中路径格式化为提示文本
    """空白路径用 @\"path\"；目录保留未闭合引号以便继续补全。"""
    路径=候选['path']+('/' if 候选.get('kind')=='directory' else '')#目录加尾斜杠
    if re.search(r'[\x00-\x1f\x7f-\x9f"]',路径):#不可表示的控制符或引号
        return None#拒绝
    需要引号=保留引号 or bool(re.search(r'\s',路径))#显式引号或含空白
    if not 需要引号:#普通形式
        return '@'+路径#@path
    if 候选.get('kind')=='directory':#目录保留开引号
        return '@"'+路径#@"dir/
    return '@"'+路径+'"'#@"path with spaces"
