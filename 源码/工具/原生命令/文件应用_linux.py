"""GIO 查询的 Linux 文件关联，配合共享 XDG 元数据与图标查找。"""
import os,re
from .桌面条目 import 桌面应用程序图标,桌面数据目录,桌面条目字段

def 桌面文件(根,标识,目录=None):
    """查找桌面 id，含从嵌套应用目录派生的 id。"""
    if 目录 is None:
        目录=根
    try:
        名字表=os.listdir(目录)
    except OSError:
        return None
    条目表=[]
    for 名 in 名字表:
        路径=os.path.join(目录,名)
        条目表.append((路径,os.path.isdir(路径)))
    for 路径,是目录 in 条目表:
        if not 是目录:
            相对=os.path.relpath(路径,根).replace(os.sep,'-')
            if 相对==标识:
                return 路径
    for 路径,是目录 in 条目表:
        if 是目录:
            找到=桌面文件(根,标识,路径)
            if 找到 is not None:
                return 找到
    return None

def linux文件应用程序(路径,信号,运行,环境):
    """从 GIO 查询全部已注册文件处理程序，不执行桌面条目命令文本。"""
    from . import 已中止
    信息=运行('gio',['info','-a','standard::content-type',路径],信号)
    mime匹配=re.search(r'standard::content-type:\s*(\S+)',信息['stdout'])
    if mime匹配 is None:
        raise ValueError('GIO did not identify the file content type')
    mime=mime匹配.group(1)
    结果=运行('env',['LC_ALL=C','gio','mime',mime],信号)
    首选匹配=re.search(r'^Default application.*:\s*(.+\.desktop)\s*$',结果['stdout'],re.M)
    首选=None if 首选匹配 is None else 首选匹配.group(1)
    标识表=[]
    if 首选 is not None:
        标识表.append(首选)
    for 行 in 结果['stdout'].splitlines():
        if re.match(r'^\s+.*\.desktop\s*$',行):
            修剪=行.strip()
            if 修剪 not in 标识表:
                标识表.append(修剪)
    家=环境.get('HOME') or os.path.expanduser('~')
    目录列表=桌面数据目录(家,环境)
    语言=(环境.get('LC_ALL') or 环境.get('LC_MESSAGES') or 环境.get('LANG') or '')
    语言=re.sub(r'\..*$','',语言)
    应用程序表=[]
    for 标识 in 标识表:
        if 已中止(信号):
            raise RuntimeError('The operation was aborted')
        条目路径=None
        for 目录 in 目录列表:
            条目路径=桌面文件(os.path.join(目录,'applications'),标识)
            if 条目路径 is not None:
                break
        if 条目路径 is None:
            continue
        with open(条目路径,'r',encoding='utf-8') as 文件:
            字段=桌面条目字段(文件.read())
        名称=字段.get('Name['+语言+']') or 字段.get('Name['+re.sub(r'_.*','',语言)+']') or 字段.get('Name')
        if 名称 is None or 字段.get('Hidden')=='true':
            continue
        图标=None if 字段.get('Icon') is None else 桌面应用程序图标(字段['Icon'],目录列表)
        import base64
        图标数据=None if 图标 is None else 'data:'+图标['contentType']+';base64,'+base64.b64encode(图标['bytes']).decode('ascii')
        应用程序表.append({'id':条目路径,'name':名称,'default':标识==首选,'icon':图标数据})
    return 应用程序表

__all__=['linux文件应用程序']
