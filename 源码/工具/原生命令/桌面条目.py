"""共享的 XDG 桌面条目字段与图标查找。"""
import os

def 桌面条目字段(文本):
    """读取主桌面条目节，不解释可执行命令。"""
    主节=False
    字段={}
    for 行 in 文本.splitlines():
        修剪=行.strip()
        if 修剪.startswith('['):
            主节=修剪=='[Desktop Entry]'
            continue
        if (not 主节) or 修剪.startswith('#'):
            continue
        分隔=修剪.find('=')
        if 分隔>0:
            字段[修剪[:分隔].strip()]=修剪[分隔+1:].strip()
    return 字段

def 桌面数据目录(家目录,环境):
    """按桌面优先级解析 XDG 应用与图标根。"""
    数据家=环境.get('XDG_DATA_HOME')
    if 数据家 is None or 数据家=='':
        数据家=os.path.join(家目录,'.local','share')
    系统目录=环境.get('XDG_DATA_DIRS')
    if 系统目录 is None or 系统目录=='':
        系统目录='/usr/local/share:/usr/share'
    return [数据家]+[段 for 段 in 系统目录.split(':') if 段]

def 读图标(路径):
    """读取已安装的 PNG 或 SVG 图标；缺席路径与目录没有像素。"""
    if 路径.endswith('.png'):
        内容类型='image/png'
    elif 路径.endswith('.svg'):
        内容类型='image/svg+xml'
    else:
        return None
    try:
        if not os.path.isfile(路径):
            return None
        with open(路径,'rb') as 文件:
            return {'bytes':文件.read(),'contentType':内容类型}
    except OSError:
        return None

def 桌面应用程序图标(名称,目录列表):
    """解析绝对图标路径或已安装的 hicolor/pixmaps 图标名。"""
    if os.path.isabs(名称):
        return 读图标(名称)
    尺寸表=['512x512','256x256','128x128','64x64','48x48','32x32']
    for 目录 in 目录列表:
        for 尺寸 in 尺寸表:
            for 扩展 in ('png','svg'):
                图标=读图标(os.path.join(目录,'icons','hicolor',尺寸,'apps',名称+'.'+扩展))
                if 图标 is not None:
                    return 图标
        可缩放=读图标(os.path.join(目录,'icons','hicolor','scalable','apps',名称+'.svg'))
        if 可缩放 is not None:
            return 可缩放
        for 扩展 in ('png','svg'):
            图标=读图标(os.path.join(目录,'pixmaps',名称+'.'+扩展))
            if 图标 is not None:
                return 图标
    return None

__all__=['桌面条目字段','桌面数据目录','桌面应用程序图标']
