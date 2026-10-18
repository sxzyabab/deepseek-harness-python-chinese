'Markdown 图片目标走已登录的文件路由'
import re
from urllib.parse import quote,unquote,urljoin
from .....工具.工作区路径 import 是否绝对工作区路径,路径展示拆分

__all__=['标记文本图片地址']

def 标记文本图片地址(基址,文档路径,目标):
    '相对目标贴在预览文件旁边。坏的百分号、协议地址和不支持的传输返回 None'
    界=len(目标)
    for 符 in ('?','#'):
        位=目标.find(符)
        if 位!=-1 and 位<界:
            界=位
    段=目标 if 界==len(目标) else 目标[:界]
    try:
        路径=unquote(段,errors='strict')
    except UnicodeDecodeError:
        return None
    if 路径=='':
        return None
    盘符=re.match(r'^[a-z]:[/\\]',路径,re.IGNORECASE) is not None
    if not 盘符 and re.match(r'^[a-z][a-z\d+.-]*:',路径,re.IGNORECASE) is not None:
        return None
    if not 是否绝对工作区路径(路径):
        if 文档路径 is None:
            return None
        路径=路径展示拆分(文档路径)['directory']+路径
    if (not 基址.startswith('http:') and not 基址.startswith('https:') and not 基址.startswith('dsh-app://app/')) or not 是否绝对工作区路径(路径):
        return None
    if 路径.startswith('//') or 路径.startswith('\\\\'):
        return None
    for 字 in 路径:
        码=ord(字)
        if 码<=0x1f or 码==0x7f:
            return None
    return urljoin(基址,'api/file?path='+quote(路径,safe=''))
