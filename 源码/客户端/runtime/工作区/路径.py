"""把工作区相对路径解析成 openPath 使用的宿主写法。

对齐上游 `runtime/src/client/workspaces/path.ts`。公开面仅中文名。
"""
import re#盘符绝对路径

__all__=['解析工作区路径']#仅中文公开名

盘符绝对=re.compile(r'^[A-Za-z]:[/\\]')#Windows 盘符绝对

def 解析工作区路径(工作目录,路径):#解析工作区路径
    """有工作区根时返回绝对路径，否则原样返回。"""
    if 路径.startswith('/') or 盘符绝对.match(路径) or 路径.startswith('\\\\'):#已是绝对或 UNC
        return 路径#原样
    if 工作目录 is None or 工作目录=='':#没有工作区根
        return 路径#原样
    根=re.sub(r'[/\\]+$','',工作目录)#去掉根尾部分隔符
    相对=re.sub(r'^[/\\]+','',路径)#去掉相对路径头部分隔符
    return 根+'/'+相对#POSIX 风格拼接
