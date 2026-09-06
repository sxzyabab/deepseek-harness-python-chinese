"""JSONL 格式辅助（对齐 upstream session-persistence-jsonl/format）。"""
import json,os#JSON 与路径
from ..会话持久化 import 持久化错误#空日志拒绝

默认压缩='zstd'#默认 zstd

def 项目目录(根,头):#项目目录
    """按会话头工作目录拼项目段；无 cwd 时用线协议占位 `_no_cwd_`。"""
    if 'cwd' in 头:#给了工作目录键
        工作目录=头['cwd']#取出
        if not 工作目录:#空或假值
            工作目录='_no_cwd_'#无 cwd 会话的路径段
    else:#缺席
        工作目录='_no_cwd_'#无 cwd 会话的路径段
    return os.path.join(根,工作目录.replace(':','_').replace(os.sep,'_'))#安全目录名

def 会话目录(根,头):#会话目录
    """项目目录下以会话 id 为名的子目录。"""
    return os.path.join(项目目录(根,头),str(头['id']))#会话子目录

def 日志路径(根,头):#日志文件路径
    """该会话 JSONL 日志的 zst 文件路径。"""
    return os.path.join(会话目录(根,头),'events.jsonl.zst')#zst 后缀

def 编码段(事件列表,打包块):#编码事件为 JSONL 文本
    """把事件列表编成 JSONL 文本；每行 UTF-8 语义由调用方再 encode。"""
    行列表=[]#行
    for 事件 in 事件列表:#逐事件
        行列表.append(json.dumps(事件,ensure_ascii=False,separators=(',',':'),allow_nan=False))#一行，中文不转义
    if len(行列表)>0:#有行
        return '\n'.join(行列表)+'\n'#行间换行且末行也换行
    return ''#空段

def 扫描日志(文本):#解析 JSONL
    """解析 JSONL 文本为首行头加后续事件。"""
    行列表=[]#非空行
    for 行 in 文本.split('\n'):#按行切
        if len(行.strip())>0:#非空
            行列表.append(行)#收集
    if len(行列表)==0:#空
        raise 持久化错误('empty session log')#拒绝
    头=json.loads(行列表[0])#首行头
    事件列表=[]#事件
    for 行 in 行列表[1:]:#后续行
        事件列表.append(json.loads(行))#解析事件
    return {'meta':头,'events':事件列表}#检查

__all__=['默认压缩','项目目录','会话目录','日志路径','编码段','扫描日志']#公开面
