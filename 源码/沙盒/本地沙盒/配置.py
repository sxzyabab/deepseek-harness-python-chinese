"""本地沙箱提供方的内部平台配置构建器。

对应上游 `@deepseek-ai/dsh-sandbox-local/profiles`。
"""
from ..沙盒 import 可写根#共用可写根推导，避免与 fs 围栏漂移
from .landlock入口 import 授权参数 as landlock授权参数#Landlock --ro/--rw 构建

def bwrap配置参数(政策):
    """为一份文件效果政策构建 bwrap 配置参数。政策是 dict。"""
    参数=['--ro-bind','/','/','--dev','/dev','--proc','/proc','--die-with-parent']#只读根加设备与进程
    if 政策['mode']=='workspace-write':#工作区可写
        参数.extend(['--tmpfs','/tmp'])#临时 /tmp
        根=政策['workspaceRoot']#工作区根
        参数.extend(['--bind',根,根])#可写绑定工作区
    return 参数#配置参数

def landlock配置参数(政策):
    """为一份文件效果政策构建 Landlock 启动器授权。政策是 dict。"""
    读写=['/dev/null']#只读模式也允许 /dev/null
    if 政策['mode']=='workspace-write':#工作区可写
        读写.extend(['/tmp',政策['workspaceRoot']])#加上 /tmp 与工作区
    return landlock授权参数({'readOnly':['/'],'readWrite':读写})#根只读，列出可写

def sbpl字符串(路径):
    """把一条路径引成 SBPL 字符串字面量。"""
    return '"'+路径.replace('\\','\\\\').replace('"','\\"')+'"'#转义反斜杠与引号

def seatbelt配置参数(政策):
    """为一份政策构建 sandbox-exec 参数与 SBPL 配置。政策是 dict。"""
    形式=[#基础形式
        '(version 1)',#SBPL 版本
        '(allow default)',#默认允许
        '(deny file-write*)',#拒绝写
        '(allow file-write* (literal '+sbpl字符串('/dev/null')+'))',#允许写 /dev/null
    ]#基础形式结束
    根列表=可写根(政策)#共用可写根
    if len(根列表)>0:#有可写根
        子路径=' '.join('(subpath '+sbpl字符串(根)+')' for 根 in 根列表)#按子路径允许写
        形式.append('(allow file-write* '+子路径+')')#追加允许写
    return ['-p',' '.join(形式)]#一条 SBPL 配置
