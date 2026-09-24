import io,re,zipfile,xml.etree.ElementTree as 元素树
from .模型 import 不支持特性表

__all__=['xlsx预览归档']

_绘图路径=re.compile(r'^xl/drawings/(?:[^/]+\.xml|_rels/[^/]+\.xml\.rels)\Z',re.IGNORECASE|re.ASCII)
_关系路径=re.compile(r'^(.*?/)?_rels/([^/]+)\.rels\Z',re.IGNORECASE|re.ASCII)

def 部件键(路径):
    """OPC 按 ASCII 大小写等价比较部件名。"""
    return re.sub(r'[A-Z]',lambda 命中:命中.group(0).lower(),路径)

def 解码xml(数据):
    """按强制 XML 编码解码，不改归档字节。"""
    if (len(数据)>=2 and 数据[0]==0xff and 数据[1]==0xfe) or (len(数据)>=2 and 数据[0]==0x3c and 数据[1]==0):
        编码='utf-16-le'
    elif (len(数据)>=2 and 数据[0]==0xfe and 数据[1]==0xff) or (len(数据)>=2 and 数据[0]==0 and 数据[1]==0x3c):
        编码='utf-16-be'
    else:
        编码='utf-8'
    return 数据.decode(编码)

def 解析部件(属主,目标):
    """解析内部关系目标，拒绝逃出包根。"""
    段表=[] if 目标.startswith('/') else 属主.split('/')[:-1]
    for 段 in 目标.split('/'):
        if 段=='' or 段=='.':
            continue
        if 段=='..':
            if len(段表)==0:
                raise RuntimeError('XLSX relationship escapes package')
            段表.pop()
        else:
            段表.append(段)
    return '/'.join(段表)

class xlsx预览归档:
    """去掉 DrawingML 部件的预览副本。"""
    def __init__(自身,字节):
        自身.字节=字节
        自身.不支持特性=set()
        自身.文件={}
        自身.部件={}
        with zipfile.ZipFile(io.BytesIO(字节)) as 包:
            for 项 in 包.infolist():
                路径=项.filename
                if 路径.endswith('/'):
                    continue
                数据=包.read(项)
                自身.文件[路径]=数据
                键=部件键(路径)
                if 键 in 自身.部件:
                    raise RuntimeError('Ambiguous XLSX part: '+路径)
                自身.部件[键]=数据

    def 去绘图(自身):
        """ExcelJS 解析前省略 DrawingML；调用方还须忽略工作表绘图引用。"""
        省略=set()
        for 路径,数据 in 自身.文件.items():
            if _绘图路径.match(路径) is not None:
                省略.add(部件键(路径))
            命中=_关系路径.match(路径)
            if 命中 is None:
                continue
            属主=(命中.group(1) or '')+命中.group(2)
            自身._扫关系(属主,数据,省略)
        留下=[(路径,数据) for 路径,数据 in 自身.文件.items() if 部件键(路径) not in 省略]
        if len(留下)==len(自身.文件):
            return 自身.字节
        缓冲=io.BytesIO()
        with zipfile.ZipFile(缓冲,'w',compression=zipfile.ZIP_STORED) as 包:
            for 路径,数据 in 留下:
                包.writestr(路径,数据)
        return 缓冲.getvalue()

    def _扫关系(自身,属主,数据,省略):
        根=元素树.fromstring(解码xml(数据))
        for 节点 in 根.iter():
            标签=节点.tag.rsplit('}',1)[-1]
            if 标签!='Relationship':
                continue
            if 节点.get('TargetMode')=='External':
                continue
            类型=节点.get('Type') or ''
            类型=类型.replace('http://purl.oclc.org/ooxml/officeDocument/relationships/','http://schemas.openxmlformats.org/officeDocument/2006/relationships/')
            是绘图=类型=='http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing'
            if not 是绘图 and 类型!='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet':
                continue
            目标=节点.get('Target')
            if not isinstance(目标,str):
                raise RuntimeError('Missing XLSX relationship target')
            完整=解析部件(属主,目标)
            内容=自身.部件.get(部件键(完整))
            if 内容 is None:
                raise RuntimeError('Missing XLSX part: '+完整)
            自身._检内容(内容)
            if 是绘图:
                省略.add(部件键(完整))
                切=完整.rfind('/')
                省略.add(部件键(完整[:切+1]+'_rels/'+完整[切+1:]+'.rels'))

    def _检内容(自身,数据):
        try:
            根=元素树.fromstring(解码xml(数据))
        except Exception:
            return
        for 节点 in 根.iter():
            标签=节点.tag.rsplit('}',1)[-1]
            if 标签=='chart':
                自身.不支持特性.add('charts')
            if 标签=='pic' or 标签=='picture':
                自身.不支持特性.add('images')
            if 标签 in ('sp','grpSp','cxnSp'):
                自身.不支持特性.add('shapes')
            if 标签=='conditionalFormatting':
                自身.不支持特性.add('conditionalFormatting')
