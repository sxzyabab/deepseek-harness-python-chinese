'经导出资源读取插件展示文案与图标，不求值插件代码'
import os,re,json
from ...基础设施.通用工具.序列化编码 import 构造dataurl
from urllib.parse import urljoin
from .配置解析.解析器 import 裸包名
from .配置解析.遗留链接 import 真实模块文件
from ...依赖.loader.内部 import 模块加载器
from ...依赖.工具 import 文件url转路径
from .异常 import 启动错误

__all__=['解析插件资源','读插件元']

语言标识=re.compile(r'^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$')
最大图标字节=256*1024
图标媒体类型={
    '.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg',
    '.jpeg':'image/jpeg','.webp':'image/webp',
}

def 文本于(值,字段):
    '非空字符串或省略'
    if 值 is None:
        return None
    if not isinstance(值,str) or 值.strip()=='':
        raise 启动错误(字段+' must be a non-empty string')
    return 值

def 对象于(值,字段):
    '必须是对象'
    if not isinstance(值,dict):
        raise 启动错误(字段+' must be an object')
    return 值

def 读对象(文件):
    '读 JSON 对象'
    try:
        文件对象=open(文件,'r',encoding='utf-8')
        try:
            内容=json.loads(文件对象.read())
        finally:
            文件对象.close()
    except Exception as 错误:
        raise 启动错误(文件+': '+str(错误))
    return 对象于(内容,文件)

def 回退文本(值):
    '非空字符串回退'
    return 值 if isinstance(值,str) and 值.strip()!='' else None

def 读图标文件(目标,标签):
    '把本地图标文件收成 data URL'
    媒体=图标媒体类型.get(os.path.splitext(目标)[1].lower())
    if 媒体 is None:
        raise 启动错误(标签+': icon must be SVG, PNG, JPEG, or WebP')
    文件=真实模块文件(目标)
    if not os.path.isfile(文件):
        raise 启动错误(标签+': icon must be a regular file')
    大小=os.path.getsize(文件)
    if 大小>最大图标字节:
        raise 启动错误(标签+': icon exceeds 256 KiB')
    文件对象=open(文件,'rb')
    try:
        字节=文件对象.read()
    finally:
        文件对象.close()
    if len(字节)>最大图标字节:
        raise 启动错误(标签+': icon exceeds 256 KiB')
    return 构造dataurl(媒体,字节)

def 断言包内(文件,包名):
    '真实文件的祖先清单必须声明该包名'
    目录=os.path.dirname(文件)
    while True:
        清单=os.path.join(目录,'package.json')
        if os.path.exists(清单) and 读对象(清单).get('name')==包名:
            return
        上一=os.path.dirname(目录)
        if 上一==目录:
            raise 启动错误(文件+': icon must remain inside its package directory')
        目录=上一

def 图标属于(说明符,包名,父网址,清单路径,值):
    '清单相对图标优先，否则用说明符/icon 导出'
    图标=None if 清单路径 is None else 文本于(值,清单路径+': icon')
    if 清单路径 is not None and 图标 is not None:
        if os.path.isabs(图标) or re.match(r'^[A-Za-z]:[\\/]',图标) or re.match(r'^[A-Za-z][A-Za-z\d+.-]*:',图标):
            raise 启动错误(清单路径+': icon must be a relative file path')
        标签=清单路径
        根=os.path.realpath(os.path.dirname(清单路径))
        目标=os.path.normpath(os.path.join(根,图标))
        相对=os.path.relpath(真实模块文件(目标),根)
        if 相对=='..' or 相对.startswith('..'+os.sep) or os.path.isabs(相对):
            raise 启动错误(标签+': icon must remain inside its manifest directory')
    else:
        导出=可选资源路径(说明符+'/icon',父网址)
        if 导出 is None:
            return None
        目标=导出
        标签=导出
        断言包内(真实模块文件(目标),包名)
    return 读图标文件(目标,标签)

def _父目录(父网址):
    '父网址对应的目录'
    文本=str(父网址 or '')
    if 文本.startswith('file:'):
        路径=文件url转路径(文本)
    else:
        路径=os.path.abspath(文本)
    if os.path.isfile(路径):
        return os.path.dirname(路径)
    return 路径

def _找包目录(名,父网址):
    '从父目录向上找 node_modules 里的包'
    当前=_父目录(父网址)
    while True:
        候选=os.path.join(当前,'node_modules',名)
        if os.path.isfile(os.path.join(候选,'package.json')):
            return 候选
        上一=os.path.dirname(当前)
        if 上一==当前:
            return None
        当前=上一

def 解析插件资源(说明符,父网址):
    '解析插件资源到本地文件，不求值插件代码'
    加载器=模块加载器.从内部()
    if 加载器 is None:
        raise 启动错误('Plugin metadata requires the Node module resolver')
    路径=None
    if 说明符.startswith('.') or 说明符.startswith('file:') or os.path.isabs(说明符):
        if 说明符.startswith('file:'):
            路径=文件url转路径(说明符)
        elif os.path.isabs(说明符):
            路径=说明符
        else:
            基=_父目录(父网址)
            if not str(父网址 or '').endswith('/') and not os.path.isdir(基):
                基=os.path.dirname(基) if os.path.isfile(基) else 基
            拼接=urljoin('file:///'+基.replace(os.sep,'/').lstrip('/')+'/',说明符)
            路径=文件url转路径(拼接) if 拼接.startswith('file:') else os.path.normpath(os.path.join(_父目录(父网址),说明符))
    else:
        包名=裸包名(说明符)
        if 包名 is not None:
            目录=_找包目录(包名,父网址)
            余=说明符[len(包名):].lstrip('/')
            if 目录 is not None:
                路径=os.path.join(目录,'package.json') if 余=='' else os.path.join(目录,*余.split('/'))
    if not 路径 or not os.path.isfile(路径):
        错误=FileNotFoundError(说明符)
        错误.code='MODULE_NOT_FOUND'
        raise 错误
    return os.path.normpath(路径)

def 缺席资源(错误):
    '解析失败是否表示资源不存在'
    码=getattr(错误,'code',None) or getattr(错误,'errno',None)
    名=type(错误).__name__
    return 码 in ('ERR_PACKAGE_PATH_NOT_EXPORTED','ERR_MODULE_NOT_FOUND','MODULE_NOT_FOUND','ENOENT','ENOTDIR',2) or 名 in ('ModuleNotFoundError','FileNotFoundError')

def 可选资源路径(说明符,父网址):
    '缺席则省略'
    try:
        return 解析插件资源(说明符,父网址)
    except Exception as 错误:
        if 缺席资源(错误):
            return None
        raise 错误

def 词典表(英文路径,说明符,父网址):
    '同目录语言文件'
    词典={}
    目录=os.path.dirname(英文路径)
    for 名 in os.listdir(目录):
        if not 名.endswith('.json'):
            continue
        资源=说明符+'/locale/'+名
        语言=名[:-5]
        if not 语言标识.match(语言):
            raise 启动错误(资源+' must use a language id as its filename')
        标识=语言.lower()
        if 标识 in 词典:
            raise 启动错误(资源+' duplicates locale '+标识)
        文件=解析插件资源(资源,父网址)
        if os.path.dirname(文件)!=目录:
            raise 启动错误(资源+': '+文件+' must share the English locale directory '+目录)
        解析=读对象(文件)
        元=None if 解析.get('meta') is None else 对象于(解析['meta'],'meta')
        词典[标识]={
            'title':文本于((元 or {}).get('title'),'meta.title'),
            'description':文本于((元 or {}).get('description'),'meta.description'),
        }
    return 词典

def 本地化文本(字段,词典,回退,最终回退):
    '合成 LocalizedText'
    条目=[]
    for 语言,字段表 in 词典.items():
        值=字段表.get(字段)
        if 值 is not None:
            条目.append((语言,值))
    if len(条目)==0:
        return 回退
    结果={'en':回退 if 回退 is not None else 最终回退}
    for 语言,值 in 条目:
        结果[语言]=值
    return 结果

def 读插件元(说明符,父网址):
    '读插件导出清单里的本地化展示文案与图标；子路径不读 package.json'
    包名=裸包名(说明符)
    if 包名 is None:
        return None
    try:
        英文路径=可选资源路径(说明符+'/locale/en.json',父网址)
        词典={} if 英文路径 is None else 词典表(英文路径,说明符,父网址)
        清单路径=可选资源路径(说明符+'/package.json',父网址) if 包名==说明符 else None
        清单=None if 清单路径 is None else 读对象(清单路径)
        标题=本地化文本('title',词典,回退文本((清单 or {}).get('name')),说明符)
        描述=本地化文本('description',词典,回退文本((清单 or {}).get('description')),'')
        文本={}
        if 标题 is not None:
            文本['title']=标题
        if 描述 is not None:
            文本['description']=描述
        图标=None
        try:
            图标=图标属于(说明符,包名,父网址,清单路径,(清单 or {}).get('icon'))
        except Exception as 错误:
            合并=dict(文本)
            合并['error']='Plugin metadata for '+说明符+': '+str(错误)
            return 合并
        if 标题 is None and 描述 is None and 图标 is None:
            return None
        结果=dict(文本)
        if 图标 is not None:
            结果['icon']=图标
        return 结果
    except Exception as 错误:
        return {'error':'Plugin metadata for '+说明符+': '+str(错误)}
