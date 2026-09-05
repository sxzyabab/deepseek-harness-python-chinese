"""每个按代寻址会话产物共享的规范原始日志基名。"""
import re#规范名匹配
from .json import 会话格式版本#导入版本校验

规范日志文件名=re.compile(r'^session(?:\.v([1-9][0-9]*))?\.jsonl$')#规范日志文件名

def 会话格式日志文件名(版本):#会话格式日志文件名
    """命名一个不可变会话格式代的原始 JSONL 日志。版本零保留原 session.jsonl；之后每代在 .jsonl 后缀前带小写数字 .vN 分量。"""
    代=会话格式版本(版本,'Session log generation version')#校验版本
    return 'session.jsonl' if 代==0 else f'session.v{代}.jsonl'#零代或带vN

def 解析会话格式日志文件名(文件名):#解析日志文件名
    """读取一个原始 JSONL 日志基名所命名的代。临时、大写、前导零、.v0 与带压缩后缀的名不规范。"""
    匹配=规范日志文件名.match(文件名)#匹配
    if 匹配 is None:#不匹配
        return None#不匹配
    if 匹配.group(1) is None:#无vN为版本零
        return 0#版本零
    版本=int(匹配.group(1))#解析数字
    上限=9007199254740991#安全整数上限
    return 版本 if isinstance(版本,int) and abs(版本)<=上限 else None#安全整数或无
