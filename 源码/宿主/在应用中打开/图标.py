'已解析应用的主机图标提取：macOS icns→PNG、Windows 关联图标、Linux hicolor/pixmaps'
import json,os,shutil,tempfile#plist JSON、路径、清理与临时目录
from ...工具.原生命令.桌面条目 import 桌面应用程序图标#Linux 图标
from .解析器 import (#解析侧共用
    取命令输出,补全内部事实,查找桌面条目,xdg数据目录列表,平台规格于,
)#解析导入

__all__=['应用图标','提取应用图标']

提取图标脚本='\n'.join([#PowerShell ExtractAssociatedIcon
    'param([string]$Source, [string]$Target)',
    '$ErrorActionPreference = "Stop"',
    'Add-Type -AssemblyName System.Drawing',
    '$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($Source)',
    'if ($null -eq $icon) { exit 1 }',
    '$bitmap = $icon.ToBitmap()',
    '$bitmap.Save($Target, [System.Drawing.Imaging.ImageFormat]::Png)',
    '',
])#脚本结束

class 应用图标:#提取结果
    '原始字节与路由应提供的媒体类型'
    def __init__(自身,字节,内容类型):#记下
        '挂上字节与 content-type'
        自身.字节=字节#原始字节
        自身.内容类型=内容类型#image/png 或 image/svg+xml

def 提取包图标png(包路径,超时毫秒,事实):#macOS .icns → 128px PNG
    '从 bundle 的 Info.plist / Resources 取 icns，经 sips 转 128px PNG'
    资源=os.path.join(包路径,'Contents','Resources')#Resources
    图标文件=None#候选名
    plistJson=取命令输出(#plutil → JSON
        'plutil',['-convert','json','-o','-',os.path.join(包路径,'Contents','Info.plist')],
        超时毫秒,事实,
    )#输出
    if plistJson is not None:#有 JSON
        try:#解析
            声明=json.loads(plistJson)#对象
            值=声明['CFBundleIconFile'] if isinstance(声明,dict) and 'CFBundleIconFile' in 声明 else None#字段
            if isinstance(值,str) and 值!='':#非空
                图标文件=值 if 值.endswith('.icns') else 值+'.icns'#补扩展
        except (json.JSONDecodeError,TypeError):#畸形
            pass#仍可扫 Resources
    if 图标文件 is None:#回退扫描
        try:#列目录
            for 名 in os.listdir(资源):#逐项
                if 名.endswith('.icns'):#命中
                    图标文件=名#收下
                    break#首个
        except OSError:#无 Resources
            return None#无图标
    if 图标文件 is None:#仍无
        return None#无
    icns=os.path.join(资源,图标文件)#完整路径
    if not os.path.exists(icns):#声明了但不在盘上
        return None#无
    工作目录=tempfile.mkdtemp(prefix='dsh-open-in-app-')#临时目录
    try:#转换
        输出png=os.path.join(工作目录,'icon.png')#输出
        if 取命令输出('sips',['-s','format','png','-Z','128',icns,'--out',输出png],超时毫秒,事实) is None:#失败
            return None#无
        try:#读出
            with open(输出png,'rb') as 文件:#打开
                return 文件.read()#字节
        except OSError:#未写出
            return None#无
    finally:#清理
        shutil.rmtree(工作目录,ignore_errors=True)#删临时

def 提取可执行图标png(可执行路径,超时毫秒,事实):#Windows 关联图标
    '经生成的 PowerShell 脚本提取可执行关联图标为 32px PNG'
    工作目录=tempfile.mkdtemp(prefix='dsh-open-in-app-')#临时目录
    try:#提取
        脚本=os.path.join(工作目录,'extract-icon.ps1')#脚本路径
        输出png=os.path.join(工作目录,'icon.png')#输出
        with open(脚本,'w',encoding='utf-8',newline='\n') as 文件:#写脚本
            文件.write(提取图标脚本)#内容
        跑过=取命令输出('powershell.exe',[#位置参数，路径不经命令行解析
            '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',脚本,可执行路径,输出png,
        ],超时毫秒,事实)#运行
        if 跑过 is None:#失败
            return None#无
        try:#读出
            with open(输出png,'rb') as 文件:#打开
                return 文件.read()#字节
        except OSError:#未写出
            return None#无
    finally:#清理
        shutil.rmtree(工作目录,ignore_errors=True)#删临时

def 提取Linux图标(桌面标识,事实):#desktop Icon=
    '从 desktop 条目的 Icon= 取 Linux 图标'
    条目=查找桌面条目(桌面标识,事实)#读条目
    if 条目 is None or 条目.图标 is None or 条目.图标=='':#无
        return None#无
    图标=桌面应用程序图标(条目.图标,xdg数据目录列表(事实))#共享查找
    if 图标 is None:#无像素
        return None#无
    return 应用图标(图标['bytes'],图标['contentType'])#包一层

def 提取应用图标(应用,已解析,超时毫秒,内部=None):#extractAppIcon
    '提取一条已解析应用在本机的图标；无则 None'
    事实=补全内部事实(内部)#补全
    if 事实.平台=='linux':#Linux
        规格=平台规格于(应用,事实.平台)#规格
        桌面标识=规格.桌面标识 if 规格 is not None else None#desktop id
        return None if 桌面标识 is None else 提取Linux图标(桌面标识,事实)#提取
    if 已解析.图标 is None:#无来源
        return None#无
    if 已解析.图标.种类=='app-bundle':#macOS bundle
        字节=提取包图标png(已解析.图标.路径,超时毫秒,事实)#转换
        return None if 字节 is None else 应用图标(字节,'image/png')#PNG
    字节=提取可执行图标png(已解析.图标.路径,超时毫秒,事实)#Windows
    return None if 字节 is None else 应用图标(字节,'image/png')#PNG
