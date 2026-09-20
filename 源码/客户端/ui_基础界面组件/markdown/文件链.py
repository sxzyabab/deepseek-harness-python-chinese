import re
from urllib.parse import unquote as 百分号解码

__all__=['解析文件链']

控制字符=re.compile(r'[\u0000-\u001f\u007f]')#控制字符
双斜杠=re.compile(r'^[\\/]{2}')#UNC
盘符=re.compile(r'^[a-z]:[\\/]',re.ASCII|re.IGNORECASE)#Windows 盘符
方案=re.compile(r'^[a-z][a-z\d+.-]*:',re.ASCII|re.IGNORECASE)#URL scheme
行片段=re.compile(r'^L([1-9]\d*)(?:-L([1-9]\d*))?\Z')#L起[-L止]

def 解析文件链(值):
    """解码本地 Markdown 文件目标与可选 GitHub 行片段；非法则 None。"""
    井=值.find('#')
    目标=值 if 井<0 else 值[:井]
    if '?' in 目标:
        return None
    try:
        路径=百分号解码(目标)
    except (UnicodeError,ValueError):
        return None
    if 路径=='' or 控制字符.search(路径) is not None:#空或控制
        return None#拒
    if 双斜杠.search(路径) is not None:#双斜杠
        return None#拒
    if 方案.search(路径) is not None and 盘符.search(路径) is None:#URL 非盘符
        return None#拒
    if 井<0:#无片段
        return {'path':路径}#仅路径
    片段=值[井+1:]#片段
    匹配=行片段.match(片段)#匹配
    if 匹配 is None:#非法
        return None#拒
    行=int(匹配.group(1))#起始
    止=行 if 匹配.group(2) is None else int(匹配.group(2))#结束
    if 止<行:#倒序
        return None#拒
    return {'path':路径,'line':行}#路径与行
