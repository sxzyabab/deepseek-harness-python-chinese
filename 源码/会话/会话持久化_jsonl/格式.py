"""JSONL 格式辅助（对齐 upstream session-persistence-jsonl/format）。"""
import json,os#JSON 与路径
默认压缩='zstd'#默认 zstd

def 项目目录(根,头):#项目目录
    工作目录=头.get('cwd') or '_no_cwd_'#cwd 段
    return os.path.join(根,工作目录.replace(':','_').replace(os.sep,'_'))#安全目录名

def 会话目录(根,头):#会话目录
    return os.path.join(项目目录(根,头),str(头.get('id')))#会话子目录

def 日志路径(根,头):#日志文件路径
    return os.path.join(会话目录(根,头),'events.jsonl.zst')#zst 后缀

def 编码段(事件们,打包块):#编码事件为 JSONL 文本
    行们=[]#行
    for 事件 in 事件们:#逐事件
        行们.append(json.dumps(事件,ensure_ascii=False,separators=(',',':')))#一行
    return '\n'.join(行们)+('\n' if len(行们)>0 else '')#拼接

def 扫描日志(文本):#解析 JSONL
    行们=[行 for 行 in 文本.split('\n') if len(行.strip())>0]#非空行
    if len(行们)==0:#空
        raise Exception('empty session log')#拒绝
    头=json.loads(行们[0])#首行头
    事件们=[json.loads(行) for 行 in 行们[1:]]#事件
    return {'meta':头,'events':事件们}#检查

__all__=['默认压缩','项目目录','会话目录','日志路径','编码段','扫描日志']#公开面
