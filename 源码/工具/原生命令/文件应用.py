"""从拥有该路径的桌面查询原生文件关联。"""
import json,os,re
from . import 运行原生命令,已中止
from .文件应用_linux import linux文件应用程序
from .文件应用_windows import windows文件应用程序
from .路径打开 import 原生文件管理器
from .类型 import 解析原生文件应用程序

MAC应用程序脚本=(
"ObjC.import('AppKit');\n"
"function run(argv) {\n"
"  var workspace = $.NSWorkspace.sharedWorkspace;\n"
"  var file = $.NSURL.fileURLWithPath(argv[0]);\n"
"  var preferred = workspace.URLForApplicationToOpenURL(file);\n"
"  var preferredPath = preferred.isNil() ? null : ObjC.unwrap(preferred.path);\n"
"  var urls = workspace.URLsForApplicationsToOpenURL(file);\n"
"  var apps = [];\n"
"  for (var i = 0; i < urls.count; i++) {\n"
"    var url = urls.objectAtIndex(i);\n"
"    var path = ObjC.unwrap(url.path);\n"
"    var image = null;\n"
"    if (argv[1] === 'icons') {\n"
"      var icon = workspace.iconForFile(path);\n"
"      var thumbnail = $.NSImage.alloc.initWithSize($.NSMakeSize(32, 32));\n"
"      thumbnail.lockFocus;\n"
"      icon.drawInRectFromRectOperationFraction($.NSMakeRect(0, 0, 32, 32), $.NSZeroRect, $.NSCompositingOperationSourceOver, 1);\n"
"      thumbnail.unlockFocus;\n"
"      var bitmap = $.NSBitmapImageRep.imageRepWithData(thumbnail.TIFFRepresentation);\n"
"      var png = bitmap.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $({}));\n"
"      image = png.isNil() ? null : 'data:image/png;base64,' + ObjC.unwrap(png.base64EncodedStringWithOptions(0));\n"
"    }\n"
"    var bundle = $.NSBundle.bundleWithURL(url);\n"
"    var bundleId = bundle.isNil() || bundle.bundleIdentifier.isNil() ? null : ObjC.unwrap(bundle.bundleIdentifier);\n"
"    var version = bundle.isNil() ? null : bundle.objectForInfoDictionaryKey('CFBundleShortVersionString');\n"
"    apps.push({\n"
"      id: path,\n"
"      name: ObjC.unwrap($.NSFileManager.defaultManager.displayNameAtPath(path)),\n"
"      default: path === preferredPath,\n"
"      icon: image,\n"
"      bundle: bundleId,\n"
"      version: version === null || version.isNil() ? null : String(ObjC.unwrap(version))\n"
"    });\n"
"  }\n"
"  return JSON.stringify(apps);\n"
"}"
)

def 确保未中止(信号):
    """信号已置位则抛。"""
    if 已中止(信号):
        raise RuntimeError('The operation was aborted')

def 原生文件应用程序(路径,信号,内部=None):
    """按操作系统偏好顺序列出已注册处理程序。"""
    return 查询文件应用程序(路径,信号,内部 or {},True)

def 查询文件应用程序(路径,信号,内部,展示):
    """查询处理程序元数据。"""
    确保未中止(信号)
    目标=桌面目标(路径,信号,内部)
    运行=内部['run'] if 'run' in 内部 else 运行原生命令
    if 目标['platform']=='linux':
        return linux文件应用程序(路径,信号,运行,内部['env'] if 'env' in 内部 else os.environ)
    if 目标['platform']=='darwin':
        结果=运行('osascript',['-l','JavaScript','-e',MAC应用程序脚本,目标['path'],'icons' if 展示 else 'handlers'],信号)
        应用程序表=解析mac应用程序(json.loads(结果['stdout']))
        return 去重mac应用程序(应用程序表) if 展示 else 应用程序表
    if 目标['platform']!='win32':
        return []
    标准输出=windows文件应用程序(目标['path'],None,信号,运行)
    return 解析原生文件应用程序(json.loads(标准输出))

def mac字段(字段值):
    """校验可选字符串字段；缺席、None 与空串读作 None。"""
    if 字段值 is None:
        return None
    if not isinstance(字段值,str):
        raise ValueError('Invalid native application entry')
    return None if len(字段值)==0 else 字段值

def 解析mac应用程序(值):
    """校验 macOS 查询输出的每一条。"""
    if not isinstance(值,list):
        raise ValueError('Invalid native application list')
    结果=[]
    for 条目 in 值:
        if not isinstance(条目,dict):
            raise ValueError('Invalid native application entry')
        包=mac字段(条目['bundle'] if 'bundle' in 条目 else None)
        版本=mac字段(条目['version'] if 'version' in 条目 else None)
        基=解析原生文件应用程序([条目])[0]
        基=dict(基)
        基['bundle']=包
        基['version']=版本
        结果.append(基)
    return 结果

def 比较版本(左,右):
    """按点分数字比较版本；非数字段作 0，缺席版本最低。"""
    if 左 is None or 右 is None:
        return 0 if 左 is 右 else (-1 if 左 is None else 1)
    甲=左.split('.')
    乙=右.split('.')
    长度=max(len(甲),len(乙))
    下标=0
    while 下标<长度:
        左段=int(甲[下标]) if 下标<len(甲) and 甲[下标].isdigit() else 0
        右段=int(乙[下标]) if 下标<len(乙) and 乙[下标].isdigit() else 0
        差=左段-右段
        if 差!=0:
            return 差
        下标+=1
    return 0

def 去重mac应用程序(应用程序表):
    """展示查询时合并同包同名副本。"""
    顺序=[]
    分组={}
    for 应用 in 应用程序表:
        if 应用['bundle'] is None:
            顺序.append(应用)
            continue
        键=应用['bundle']+'\0'+应用['name']
        下标=分组.get(键)
        if 下标 is None:
            分组[键]=len(顺序)
            顺序.append(应用)
            continue
        持有=顺序[下标]
        if 持有['default']:
            continue
        if 应用['default'] or 比较版本(应用['version'],持有['version'])>0:
            顺序[下标]=应用
    return [{'id':项['id'],'name':项['name'],'default':项['default'],'icon':项['icon']} for 项 in 顺序]

def 打开原生文件应用程序(路径,应用程序,信号,内部=None):
    """在当前已注册处理程序中打开文件。"""
    if 内部 is None:
        内部={}
    目标=桌面目标(路径,信号,内部)
    运行=内部['run'] if 'run' in 内部 else 运行原生命令
    if 目标['platform']=='win32':
        windows文件应用程序(目标['path'],应用程序,信号,运行)
        return
    应用表=查询文件应用程序(路径,信号,内部,False)
    if not any(项['id']==应用程序 for 项 in 应用表):
        raise ValueError('Application is not registered for this file')
    if 目标['platform']=='linux':
        运行('gio',['launch',应用程序,路径],信号)
    else:
        运行('open',['-a',应用程序,路径],信号)

def 桌面目标(路径,信号,内部):
    """解析拥有该文件的桌面，含从 WSL 到达的 Windows 应用。"""
    确保未中止(信号)
    系统=内部['platform'] if 'platform' in 内部 else ('win32' if os.name=='nt' else __import__('platform').system().lower())
    if 系统=='windows':
        系统='win32'
    if 系统=='macos':
        系统='darwin'
    if 系统=='linux' and 原生文件管理器(内部)=='explorer':
        译=(内部['run'] if 'run' in 内部 else 运行原生命令)('wslpath',['-w',路径],信号)
        确保未中止(信号)
        windows路径=re.sub(r'[\r\n]+$','',译['stdout'])
        if windows路径=='':
            raise ValueError('wslpath returned no Windows path')
        return {'platform':'win32','path':windows路径}
    return {'platform':系统,'path':路径}

__all__=['原生文件应用程序','打开原生文件应用程序']
