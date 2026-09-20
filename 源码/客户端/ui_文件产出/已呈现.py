from urllib.parse import urlencode as 编查询

__all__=[#仅中文公开名
    '呈现打开路径',
    '呈现宿主路径',
    '是否已呈现宿主',
    '是否已呈现文件',
    '已呈现文件网址',
    '是否已呈现数据',
    '路径末段',
]#公开面结束

呈现打开路径='/api/present.open'#打开路由
呈现宿主路径='/api/present.host'#宿主路由

def 是否已呈现宿主(值):#校验桌面元数据
    """校验经 HTTP 收到的桌面元数据。值须为 dict。"""
    if not isinstance(值,dict):#须映射
        return False#否
    if 'name' not in 值 or not isinstance(值['name'],str):#名
        return False#否
    if 'available' not in 值 or not isinstance(值['available'],bool):#可用性；排除 bool 子类误判由 isinstance(bool) 保证
        return False#否
    管理器=值['fileManager'] if 'fileManager' in 值 else None#管理器
    return 管理器 is None or 管理器 in ('finder','explorer','directory')#合法取值

def 是否已呈现文件(值):#校验文件声明
    """校验从会话日志读出的文件声明。值须为 dict。"""
    if not isinstance(值,dict):#须映射非列表
        return False#否
    路径=值['path'] if 'path' in 值 else None#路径
    if not isinstance(路径,str) or len(路径.strip())==0:#非空白
        return False#否
    if 'description' not in 值:#无描述
        return True#合法
    return isinstance(值['description'],str)#描述须字符串

def 已呈现文件网址(会话标识,序号,下标):#建造动作 URL
    """为已声明文件建造已认证坐标。"""
    return 呈现打开路径+'?'+编查询({'sessionId':会话标识,'seq':str(序号),'index':str(下标)})

def 是否已呈现数据(值):#校验交付事件
    """在读取回合或文件声明前校验交付事件。值须为 dict。"""
    if not isinstance(值,dict):#须映射
        return False#否
    回合=值['turn'] if 'turn' in 值 else None#回合
    调用=值['callId'] if 'callId' in 值 else None#调用
    文件表=值['files'] if 'files' in 值 else None#文件
    if not isinstance(回合,int) or isinstance(回合,bool) or 回合<1:#回合 ≥ 1；排除 bool
        return False#否
    if not isinstance(调用,str) or len(调用)==0:#调用非空
        return False#否
    return isinstance(文件表,list)#须列表

def 路径末段(路径):#取末段
    """正斜杠或反斜杠分隔的末段；无分隔则整串。"""
    位置=max(路径.rfind('/'),路径.rfind('\\'))#最后分隔
    return 路径 if 位置==-1 else 路径[位置+1:]#末段
