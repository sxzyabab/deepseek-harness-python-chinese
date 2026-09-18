"""校验跨宿主路由的工作区改动记录，并寻址其摘要、对比与原生打开动作。"""
from urllib.parse import quote as 百分号编码,urlencode as 编查询#URL

__all__=[#仅中文公开名
    '已改文件路径','改动对比路径','改动打开路径','改动审阅地址前缀',
    '是否已改文件','是否改动摘要','是否改动对比','是否改动事件',
    '改动摘要网址','改动对比网址','已改文件网址','改动审阅地址','解析改动审阅地址',
]#公开面结束

已改文件路径='/api/changes.summary'#摘要 GET
改动对比路径='/api/changes.diff'#对比 GET
改动打开路径='/api/changes.open'#打开 POST
改动审阅地址前缀='dsh-resource://changes-review/session/'#审阅地址前缀

def _是否记录(值):#对象且非列表
    """窄化为 dict。"""
    return isinstance(值,dict)#是

def 是否已改文件(值):#校验一条已改文件
    """路径、展示名与行数齐全。"""
    if not _是否记录(值):#非对象
        return False#否
    路径=值['path'] if 'path' in 值 else None#路径
    展示=值['display'] if 'display' in 值 else None#展示
    新增=值['added'] if 'added' in 值 else None#增
    删除=值['deleted'] if 'deleted' in 值 else None#删
    二进制=值['binary'] if 'binary' in 值 else None#二进制
    过大=值['oversized'] if 'oversized' in 值 else None#过大
    if not isinstance(路径,str) or len(路径)==0:#路径
        return False#否
    if not isinstance(展示,str) or len(展示)==0:#展示
        return False#否
    if not isinstance(新增,int) or not isinstance(删除,int):#行数
        return False#否
    if 二进制 is not None and 二进制 is not True:#二进制只能 true
        return False#否
    if 过大 is not None and 过大 is not True:#过大只能 true
        return False#否
    return True#是

def 是否改动摘要(值):#校验摘要
    """回合、完整文件表、总数与行合计。"""
    if not _是否记录(值):#非对象
        return False#否
    回合=值['turn'] if 'turn' in 值 else None#回合
    文件=值['files'] if 'files' in 值 else None#文件
    总数=值['total'] if 'total' in 值 else None#总数
    新增=值['added'] if 'added' in 值 else None#增
    删除=值['deleted'] if 'deleted' in 值 else None#删
    if not isinstance(回合,int) or 回合<1:#回合
        return False#否
    if not isinstance(总数,int) or not isinstance(新增,int) or not isinstance(删除,int):#计数
        return False#否
    if not isinstance(文件,list) or not all(是否已改文件(项) for 项 in 文件):#文件表
        return False#否
    return True#是

def _是否块(值):#校验一块
    """行号非负且行以 + - 空格起。"""
    if not _是否记录(值):#非对象
        return False#否
    for 键 in ('oldStart','oldLines','newStart','newLines'):#行号
        字段=值[键] if 键 in 值 else None#字段
        if not isinstance(字段,int) or 字段<0:#非法
            return False#否
    行表=值['lines'] if 'lines' in 值 else None#行
    if not isinstance(行表,list):#非列表
        return False#否
    for 行 in 行表:#每行
        if not isinstance(行,str) or len(行)==0 or 行[0] not in '+ -':#前缀
            return False#否
    return True#是

def 是否改动对比(值):#校验对比
    """文本对比带块，或二进制/过大拒绝。"""
    if not _是否记录(值):#非对象
        return False#否
    种=值['kind'] if 'kind' in 值 else None#种
    路径=值['path'] if 'path' in 值 else None#路径
    展示=值['display'] if 'display' in 值 else None#展示
    if not isinstance(路径,str) or len(路径)==0 or not isinstance(展示,str) or len(展示)==0:#坐标
        return False#否
    if 种 in ('binary','oversized'):#拒绝种
        return True#是
    if 种!='text':#非文本
        return False#否
    之前=值['before'] if 'before' in 值 else None#之前
    之后=值['after'] if 'after' in 值 else None#之后
    粗=值['coarse'] if 'coarse' in 值 else None#粗
    块表=值['hunks'] if 'hunks' in 值 else None#块
    if not isinstance(之前,bool) or not isinstance(之后,bool) or not isinstance(粗,bool):#布尔
        return False#否
    if not isinstance(块表,list) or not all(_是否块(块) for 块 in 块表):#块
        return False#否
    return True#是

def 是否改动事件(值):#校验 workspace/changes 数据
    """命名回合。"""
    if not _是否记录(值):#非对象
        return False#否
    回合=值['turn'] if 'turn' in 值 else None#回合
    return isinstance(回合,int) and 回合>=1#合法

def 改动摘要网址(会话标识,序号):#摘要 URL
    """同源摘要坐标。"""
    return 已改文件路径+'?'+编查询({'sessionId':会话标识,'seq':str(序号)})#查询

def 改动对比网址(会话标识,序号,下标):#对比 URL
    """同源对比坐标。"""
    return 改动对比路径+'?'+编查询({'sessionId':会话标识,'seq':str(序号),'index':str(下标)})#查询

def 已改文件网址(会话标识,序号,下标):#打开 URL
    """同源打开坐标。"""
    return 改动打开路径+'?'+编查询({'sessionId':会话标识,'seq':str(序号),'index':str(下标)})#查询

def 改动审阅地址(坐标):#审阅资源地址
    """dsh-resource://changes-review/session/…。"""
    return 改动审阅地址前缀+百分号编码(坐标['sessionId'],safe='')+'/'+str(坐标['seq'])+'/'+str(坐标['turn'])#地址

def 解析改动审阅地址(地址):#读回坐标
    """非本包铸造则 None。"""
    if not isinstance(地址,str) or not 地址.startswith(改动审阅地址前缀):#前缀
        return None#否
    段=地址[len(改动审阅地址前缀):].split('/')#三段
    if len(段)!=3:#形态
        return None#否
    会话原文,序号文,回合文=段#拆
    if 会话原文=='' or not 序号文.isdigit() or not (回合文.isdigit() and int(回合文)>=1):#形态
        return None#否
    try:#解码
        from urllib.parse import unquote as 百分号解码#解码
        会话=百分号解码(会话原文)#会话
    except Exception:#畸形百分号
        return None#否
    return {'sessionId':会话,'seq':int(序号文),'turn':int(回合文)}#坐标
