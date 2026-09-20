import re
from .错误 import 团队错误

__all__=['必填文本','写范围']

盘符前缀=re.compile(r'^[a-z]:',re.I|re.ASCII)

def 必填文本(值,字段,最大长度):
    """规范化一条必填的人工撰写字符串。"""
    文本=值.strip()
    if len(文本)==0:
        raise 团队错误(字段+' must be non-empty','TEAM_INVALID_ARGUMENT')
    if len(文本)>最大长度:
        raise 团队错误(字段+' exceeds '+str(最大长度)+' characters','TEAM_INVALID_ARGUMENT')
    return 文本

def 写范围(值):
    """规范化一个工作区相对路径前缀，不把它当锁。"""
    规范化=值.replace('\\','/')
    if 规范化.startswith('./'):
        规范化=规范化[2:]
    规范化=规范化.rstrip('/')
    分段=规范化.split('/')
    if (len(规范化)==0 or 规范化.startswith('/') or 盘符前缀.match(规范化) is not None
            or any(段=='' or 段=='.' or 段=='..' for 段 in 分段)):
        raise 团队错误('invalid workspace-relative write scope '+repr(值),'TEAM_INVALID_WRITE_SCOPE')
    return 规范化
