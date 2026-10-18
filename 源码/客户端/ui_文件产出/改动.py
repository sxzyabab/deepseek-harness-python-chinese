'校验跨宿主路由的工作区改动记录，并寻址其摘要、对比与原生打开'
import re
from urllib.parse import quote, unquote, urlencode
from ...基础设施.通用工具 import 是否整值数,是否非负安全整数,是否正安全整数,最大安全整数

__all__=[
    '已改文件路径','改动对比路径','改动打开路径',
    '已改文件路由','改动对比路由','改动打开路由','改动审阅地址前缀',
    '是否已改文件','是否改动摘要','是否改动对比','是否改动事件',
    '改动摘要网址','改动对比网址','已改文件网址','改动审阅地址','解析改动审阅地址',
]

已改文件路径='/api/changes.summary'
改动对比路径='/api/changes.diff'
改动打开路径='/api/changes.open'
已改文件路由=已改文件路径[1:]
改动对比路由=改动对比路径[1:]
改动打开路由=改动打开路径[1:]
改动审阅地址前缀='dsh-resource://changes-review/session/'
序号形态=re.compile(r'^\d+$')
回合形态=re.compile(r'^[1-9]\d*$')
行首形态=re.compile(r'^[+ -]')


def 是否记录(值):
    '普通对象，排除数组和空'
    return isinstance(值,dict)


def 是安全整数(值):
    '双精度可无损表示的整数，含负数，排除布尔'
    if not 是否整值数(值):
        return False
    return abs(int(值))<=最大安全整数


def 是否已改文件(值):
    '路径、展示名与行数齐全'
    if not 是否记录(值):
        return False
    return isinstance(值.get('path'),str) and len(值.get('path'))>0 and isinstance(值.get('display'),str) and len(值.get('display'))>0 and 是安全整数(值.get('added')) and 是安全整数(值.get('deleted')) and ('binary' not in 值 or 值.get('binary') is True) and ('oversized' not in 值 or 值.get('oversized') is True)


def 是否改动摘要(值):
    '回合、完整文件表和行数合计'
    if not 是否记录(值):
        return False
    文件表=值.get('files')
    if not (是否正安全整数(值.get('turn')) and 是否非负安全整数(值.get('total')) and 是否非负安全整数(值.get('added')) and 是否非负安全整数(值.get('deleted')) and isinstance(文件表,list)):
        return False
    for 文件 in 文件表:
        if not 是否已改文件(文件):
            return False
    return True


def 是否改动对比(值):
    '文本对比、二进制或过大'
    if not 是否记录(值):
        return False
    if not isinstance(值.get('path'),str) or len(值.get('path'))==0 or not isinstance(值.get('display'),str) or len(值.get('display'))==0:
        return False
    种类=值.get('kind')
    if 种类=='binary' or 种类=='oversized':
        return True
    if 种类!='text':
        return False
    块表=值.get('hunks')
    if not (isinstance(值.get('before'),bool) and isinstance(值.get('after'),bool) and isinstance(值.get('coarse'),bool) and isinstance(块表,list)):
        return False
    for 块 in 块表:
        if not 是否记录(块):
            return False
        行号齐=True
        for 字段 in ('oldStart','oldLines','newStart','newLines'):
            if not 是否非负安全整数(块.get(字段)):
                行号齐=False
        if not 行号齐:
            return False
        行表=块.get('lines')
        if not isinstance(行表,list):
            return False
        for 行 in 行表:
            if not isinstance(行,str) or 行首形态.match(行) is None:
                return False
    return True


def 是否改动事件(值):
    'workspace/changes 事件至少带回合号'
    return 是否记录(值) and 是否正安全整数(值.get('turn'))


def 改动摘要网址(会话标识,序号):
    '一条宣告的摘要地址'
    return 已改文件路由+'?'+urlencode({'sessionId':str(会话标识),'seq':str(序号)})


def 改动对比网址(会话标识,序号,下标):
    '所列文件的对比地址'
    return 改动对比路由+'?'+urlencode({'sessionId':str(会话标识),'seq':str(序号),'index':str(下标)})


def 已改文件网址(会话标识,序号,下标):
    '已改文件的原生打开地址'
    return 改动打开路由+'?'+urlencode({'sessionId':str(会话标识),'seq':str(序号),'index':str(下标)})


def 改动审阅地址(坐标):
    '右侧边栏里这一轮审阅的资源地址'
    return 改动审阅地址前缀+quote(str(坐标['sessionId']),safe="-_.!~*'()")+'/'+str(坐标['seq'])+'/'+str(坐标['turn'])


def 解析改动审阅地址(地址):
    '从审阅地址读回坐标。别的地址返回 None'
    if not isinstance(地址,str) or not 地址.startswith(改动审阅地址前缀):
        return None
    段=地址[len(改动审阅地址前缀):].split('/')
    if len(段)!=3:
        return None
    会话段,序号段,回合段=段
    if 会话段=='' or 序号形态.match(序号段) is None or 回合形态.match(回合段) is None:
        return None
    下标=0
    长度=len(会话段)
    while 下标<长度:
        if 会话段[下标]=='%':
            if 下标+2>=长度:
                return None
            十六=会话段[下标+1:下标+3]
            if any(字 not in '0123456789abcdefABCDEF' for 字 in 十六):
                return None
            下标+=3
        else:
            下标+=1
    return {'sessionId':unquote(会话段),'seq':int(序号段),'turn':int(回合段)}
