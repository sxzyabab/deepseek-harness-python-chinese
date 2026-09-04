"""由 Team roster 与任务命令共享的输入规范化。

对齐上游 `agent-team/src/validation.ts`。公开面仅中文名。
"""
import re#路径段校验
from .错误 import 团队错误#领域错误

__all__=['必填文本','写范围']#仅中文公开名

盘符前缀=re.compile(r'^[a-z]:',re.I)#盘符绝对路径

def 必填文本(值,字段,最大长度):#必填人工字符串
    """规范化一条必填的人工撰写字符串。"""
    文本=值.strip()#修剪
    if len(文本)==0:#空拒
        raise 团队错误(字段+' must be non-empty','TEAM_INVALID_ARGUMENT')#空拒
    if len(文本)>最大长度:#超长
        raise 团队错误(字段+' exceeds '+str(最大长度)+' characters','TEAM_INVALID_ARGUMENT')#超长拒
    return 文本#通过

def 写范围(值):#工作区相对路径前缀
    """规范化一个工作区相对路径前缀，不把它当锁。"""
    规范化=值.replace('\\','/')#规范斜杠
    if 规范化.startswith('./'):#去 ./ 前缀
        规范化=规范化[2:]#剥前缀
    规范化=规范化.rstrip('/')#去尾斜杠
    分段=规范化.split('/')#分段
    if (len(规范化)==0 or 规范化.startswith('/') or 盘符前缀.match(规范化) is not None#绝对或盘符
            or any(段=='' or 段=='.' or 段=='..' for 段 in 分段)):#空或相对段
        raise 团队错误('invalid workspace-relative write scope '+repr(值),'TEAM_INVALID_WRITE_SCOPE')#非法前缀
    return 规范化#通过
