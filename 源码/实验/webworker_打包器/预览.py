"""浏览器 Preview 数据叠加的 Node 侧会话准备。"""
import json,os,re,tempfile,shutil
from ...会话.会话格式 import 是否会话格式json对象,解析会话格式日志文件名,会话格式日志文件名
from ...会话.会话格式目录 import 创建带子项的会话格式目录,既往会话格式目录,会话格式目录
from ...会话.会话格式_v3到v4 import 历史子名录源
from .打包 import 打包虚拟文件系统叠加

def 打包预览夹具(树列表):
    """打包 Preview 数据：已提交源字节留在叠加层，只恢复每会话最新规范原始代。"""
    原始=打包虚拟文件系统叠加(树列表)
    后继={}
    来源表=选中会话(原始['files'])
    已解码=[]
    for 源 in 来源表:
        文本=源['bytes'].decode('utf-8')
        if not 文本.endswith('\n'):
            raise ValueError('preview fixture: '+源['path']+' has a torn physical tail')
        行列表=文本[:-1].split('\n')
        头行=行列表[0] if len(行列表)>0 else ''
        其余=行列表[1:]
        头=json.loads(头行)
        if not 是否会话格式json对象(头) or 头.get('version')!=源['version'] or 头.get('id')!=源['id']:
            raise ValueError('preview fixture: '+源['path']+' disagrees with its Session header')
        名录=既往会话格式目录 if 源['version']<=3 else 会话格式目录
        恢复=名录.createRestore(头,{'recovery':'strict','validation':'current'})
        事件表=[json.loads(行) for 行 in 其余]
        for 事件 in 事件表:
            恢复.decodeRow(事件)
        项=dict(源)
        项['header']=头
        项['events']=事件表
        项['artifact']=恢复.finish()
        已解码.append(项)
    当前版本=会话格式目录.currentVersion
    for 源 in 已解码:
        if 源['version']==当前版本:
            continue
        子项=[]
        for 孩子 in 已解码:
            同父=os.path.dirname(孩子['directory'].replace('\\','/'))==os.path.dirname(源['directory'].replace('\\','/'))
            产物头=孩子['artifact']['header']
            if 同父 and 产物头.get('parentSession')==源['id'] and 产物头.get('origin')=='subagent':
                子源=dict(历史子名录源(孩子['artifact']))
                子源['sourcePath']=孩子['path']
                子项.append(子源)
        恢复=创建带子项的会话格式目录(子项).createRestore(源['header'],{'recovery':'strict','validation':'current'})
        for 事件 in 源['events']:
            恢复.decodeRow(事件)
        产物=恢复.finish()
        编码头=会话格式目录.encodeCurrentHeader(产物['header'],产物['inheritedEventCount'])
        编码事件=[会话格式目录.encodeCurrentEvent(事件) for 事件 in 产物['events']]
        校验=会话格式目录.createRestore(编码头,{'recovery':'strict','validation':'current'})
        for 事件 in 编码事件:
            校验.decodeRow(事件)
        校验.finish()
        路径=源['directory'].replace('\\','/')+'/'+会话格式日志文件名(当前版本)
        后继[路径]=''.join(json.dumps(行,ensure_ascii=False,separators=(',',':'))+'\n' for 行 in [编码头]+编码事件)
    if len(后继)==0:
        return 原始
    目录=tempfile.mkdtemp(prefix='dsh-preview-sessions-')
    try:
        for 镜像路径,内容 in 后继.items():
            磁盘路径=os.path.join(目录,镜像路径[len('home/sessions/'):].replace('/',os.sep))
            os.makedirs(os.path.dirname(磁盘路径),exist_ok=True)
            标志=os.O_WRONLY|os.O_CREAT|os.O_EXCL
            句柄=os.open(磁盘路径,标志,0o666)
            try:
                os.write(句柄,内容.encode('utf-8'))
            finally:
                os.close(句柄)
        return 打包虚拟文件系统叠加(list(树列表)+[{'mount':'home/sessions','directory':目录}])
    finally:
        shutil.rmtree(目录,ignore_errors=True)

def 选中会话(文件表):
    """每个会话目录只保留最新规范原始代。"""
    选中={}
    形态=re.compile(r'^home/sessions/[^/]+/([^/]+)/(session(?:\..*)?\.jsonl(?:\.zstd)?)$')
    for 路径,字节 in 文件表.items():
        匹配=形态.match(路径)
        if 匹配 is None:
            continue
        版本=解析会话格式日志文件名(匹配.group(2))
        if 版本 is None:
            raise ValueError('preview fixture: '+路径+' must name a canonical raw Session generation')
        目录=os.path.dirname(路径).replace('\\','/')
        先前=选中.get(目录)
        if 先前 is None or 先前['version']<版本:
            选中[目录]={'path':路径,'directory':目录,'id':匹配.group(1),'version':版本,'bytes':字节}
    return list(选中.values())

__all__=['打包预览夹具']
