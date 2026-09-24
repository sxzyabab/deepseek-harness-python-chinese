import re
from urllib.parse import quote,unquote
from .....工具.工作区路径 import 是否绝对工作区路径,路径展示拆分

__all__=['标记文本图片网址']

_窗盘符=re.compile(r'^[a-z]:[/\\]',re.IGNORECASE|re.ASCII)
_带方案=re.compile(r'^[a-z][a-z\d+.-]*:',re.IGNORECASE|re.ASCII)
_控制=re.compile(r'[\u0000-\u001f\u007f]')

def 标记文本图片网址(基址,文档路径,目的地):
    """相对目的地解析到预览文件旁，再走鉴权文件路由。"""
    缀=re.search(r'[?#]',目的地)
    原=目的地 if 缀 is None else 目的地[:缀.start()]
    try:
        路径=unquote(原)
    except Exception:
        return None
    if 路径=='':
        return None
    窗盘=_窗盘符.search(路径) is not None
    if not 窗盘 and _带方案.search(路径) is not None:
        return None
    if not 是否绝对工作区路径(路径):
        if 文档路径 is None:
            return None
        路径=路径展示拆分(文档路径)['directory']+路径
    if not 基址.startswith('http://') and not 基址.startswith('https://'):
        return None
    if not 是否绝对工作区路径(路径):
        return None
    if 路径.startswith('//') or 路径.startswith('\\\\') or _控制.search(路径) is not None:
        return None
    根=基址 if 基址.endswith('/') else 基址+'/'
    return 根+'api/file?path='+quote(路径,safe='')
