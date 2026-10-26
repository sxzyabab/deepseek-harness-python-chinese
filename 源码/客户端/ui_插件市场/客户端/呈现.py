'发现页的查询和展示。界面句子不在这里'
import datetime
from urllib.parse import urlparse

__all__=[
    '初始查询','带文本','已声明查询','显示声明','呈现版本','来源事实','索引标签','条目标题','格式日期','可安装',
]

初始查询={'text':'','category':None,'labels':[],'sort':{'kind':'index'}}

def 带文本(查询,文本):
    '空文本写成字之后，索引序改成相关序。字清空后相关序回到索引序。已经选过的序保持'
    原先空白=查询['text'].strip()==''
    现在空白=文本.strip()==''
    排序=查询['sort']
    if 原先空白 and 现在空白 is not True and 排序.get('kind')=='index':
        排序={'kind':'relevance'}
    elif 现在空白 and 排序.get('kind')=='relevance':
        排序={'kind':'index'}
    return {'text':文本,'category':查询['category'],'labels':查询['labels'],'sort':排序}

def 已声明查询(查询,元数据):
    '丢掉索引不再声明的分类、标签和排序键。没变就返回原查询'
    分类表=元数据.get('categories') or {}
    标签表=元数据.get('labels') or {}
    排序键表=元数据.get('sortKeys') or {}
    分类=查询['category']
    if 分类 is not None and 分类 not in 分类表:
        分类=None
    标签=[]
    for 项 in 查询['labels']:
        if 项 in 标签表:
            标签.append(项)
    排序=查询['sort']
    if 排序.get('kind')=='key' and 排序.get('id') not in 排序键表:
        排序={'kind':'index'}
    未变=分类==查询['category'] and len(标签)==len(查询['labels']) and 排序 is 查询['sort']
    if 未变:
        return 查询
    return {'text':查询['text'],'category':分类,'labels':标签,'sort':排序}

def 显示声明(声明表,解析文本,语言):
    '按标题码点，再按标识。语言不改变码点序'
    if not isinstance(语言,str):
        语言=''
    列=[]
    for 标识,声明 in 声明表.items():
        列.append({'id':标识,'title':解析文本(声明['title']),'declaration':声明})
    def 排序键(项):
        '标题在前，标识在后'
        return (项['title'],项['id'],语言)
    列.sort(key=排序键)
    return 列

def 呈现版本(条目):
    '默认版本。没有兼容的默认版本时用列表里的第一个'
    for 版本 in 条目['versions']:
        if 版本['version']==条目['defaultVersion']:
            return 版本
    return 条目['versions'][0]

def 来源事实(名称,版本):
    'npm 给出包和注册表。Git 给出仓库、完整提交和目录'
    来源=版本['source']
    if 来源['type']=='npm':
        列=[{'kind':'package','value':名称+'@'+版本['version']}]
        if 来源.get('registry') is not None:
            列.append({'kind':'registry','value':来源['registry']})
        return 列
    列=[
        {'kind':'repository','value':来源['url']},
        {'kind':'commit','value':来源['commit']},
    ]
    if 来源.get('path') is not None:
        列.append({'kind':'directory','value':来源['path']})
    return 列

def 索引标签(索引,解析文本):
    '读到标题用标题。否则用主机。解析不了的地址按原文'
    if 索引.get('title') is not None:
        return 解析文本(索引['title'])
    网址=索引['url']
    解析=urlparse(网址)
    if 解析.scheme!='' and 解析.netloc!='':
        return 解析.netloc
    return 网址

def 条目标题(条目,面):
    '没有本地化标题时用包名'
    if 条目.get('title') is None:
        return 条目['name']
    return 面['resolveText'](条目['title'])

def 格式日期(时间戳,语言,样式):
    '中文用年月日。其余用 ISO 日期。时间戳单位是秒'
    if not isinstance(语言,str):
        语言=''
    时刻=datetime.datetime.fromtimestamp(时间戳,datetime.timezone.utc)
    if 语言.lower().startswith('zh'):
        if 样式=='long':
            return str(时刻.year)+'年'+str(时刻.month)+'月'+str(时刻.day)+'日'
        return str(时刻.year)+'年'+str(时刻.month)+'月'+str(时刻.day)+'日'
    return 时刻.date().isoformat()

def 可安装(兼容):
    '兼容，或者已经有豁免'
    return 兼容.get('compatible') is True or 兼容.get('exempted') is True
