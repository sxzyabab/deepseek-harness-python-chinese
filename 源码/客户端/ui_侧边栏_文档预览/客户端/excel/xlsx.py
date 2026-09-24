import io,zipfile,xml.etree.ElementTree as 元素树
from .错误 import 表格预览错误
from .模型 import 不支持特性表,格式化单元格,初始选区
from .xlsx归档 import xlsx预览归档,解码xml

__all__=['转换xlsx']

_列字母=re.compile(r'^([A-Z]+)',re.ASCII)

def 列号(地址):
    命中=_列字母.match(地址)
    if 命中 is None:
        return 0
    号=0
    for 字 in 命中.group(1):
        号=号*26+(ord(字)-64)
    return 号-1

def 行号(地址):
    数字=''
    for 字 in 地址:
        if '0'<=字<='9':
            数字+=字
    return int(数字)-1 if 数字 else 0

def 转换xlsx(字节,上限):
    """解码 xlsx 显示单元格，省略绘图且不重算公式。"""
    try:
        归档=xlsx预览归档(字节)
        预览=归档.去绘图()
    except Exception as 错误:
        raise 表格预览错误('invalid') from 错误
    try:
        表=转换xlsx字节(预览,上限,归档.不支持特性)
    except 表格预览错误:
        raise
    except Exception as 错误:
        raise 表格预览错误('invalid') from 错误
    return 表

def 转换xlsx字节(字节,上限,不支持):
    with zipfile.ZipFile(io.BytesIO(字节)) as 包:
        名表={部件.lower():部件 for 部件 in 包.namelist()}
        def 读(路径):
            真=名表.get(路径.lower())
            if 真 is None:
                return None
            return 包.read(真)
        共享=读共享(读('xl/sharedStrings.xml'))
        簿=读('xl/workbook.xml')
        if 簿 is None:
            raise 表格预览错误('invalid')
        表名,可见=读工作簿(簿)
        if not any(可见):
            raise 表格预览错误('invalid')
        面积=0
        缺结果=0
        已活动=False
        工作表=[]
        序=0
        for 名,路径 in 表名:
            数据=读(路径)
            if 数据 is None:
                raise 表格预览错误('invalid')
            行数,列数,单元格,配置,缺=读工作表(数据,共享,上限)
            面积+=行数*列数
            if 面积>上限['maxCells']:
                raise 表格预览错误('tooLarge')
            缺结果+=缺
            显示=可见[序] if 序<len(可见) else True
            状态=1 if 显示 and not 已活动 else 0
            if 显示:
                已活动=True
            工作表.append({
                'id':str(序+1),'name':名,'order':序,'status':状态,'hide':0 if 显示 else 1,
                'row':行数,'column':列数,'config':配置,'celldata':单元格,
                'luckysheet_select_save':初始选区(配置),
            })
            序+=1
    特性=[项 for 项 in 不支持特性表 if 项 in 不支持]
    return {'sheets':工作表,'missingResults':缺结果,'unsupportedFeatures':特性}

def 读共享(数据):
    if 数据 is None:
        return []
    根=元素树.fromstring(解码xml(数据))
    表=[]
    for 项 in 根:
        if 项.tag.rsplit('}',1)[-1]!='si':
            continue
        表.append(''.join(节点.text or '' for 节点 in 项.iter() if 节点.tag.rsplit('}',1)[-1] in ('t','si')))
    return 表

def 读工作簿(数据):
    根=元素树.fromstring(解码xml(数据))
    表=[]
    可见=[]
    for 节点 in 根.iter():
        if 节点.tag.rsplit('}',1)[-1]!='sheet':
            continue
        名=节点.get('name') or 'Sheet'
        状态=节点.get('state')
        可见.append(状态!='hidden' and 状态!='veryHidden')
        标识=节点.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') or 节点.get('id')
        表.append((名,标识))
    关系=None
    return [(名,'xl/worksheets/sheet'+str(下+1)+'.xml') for 下,(名,_) in enumerate(表)],可见

def 读工作表(数据,共享,上限):
    根=元素树.fromstring(解码xml(数据))
    行数=1
    列数=1
    单元格=[]
    配置={'merge':{},'rowlen':{},'columnlen':{},'rowhidden':{},'colhidden':{}}
    缺=0
    for 节点 in 根.iter():
        标签=节点.tag.rsplit('}',1)[-1]
        if 标签=='mergeCell':
            引用=节点.get('ref') or 'A1'
            段=引用.split(':')
            起=段[0]
            止=段[-1]
            合并={'r':行号(起),'c':列号(起),'rs':行号(止)-行号(起)+1,'cs':列号(止)-列号(起)+1}
            配置['merge'][str(合并['r'])+'_'+str(合并['c'])]=合并
            行数=行数 if 行数>=合并['r']+合并['rs'] else 合并['r']+合并['rs']
            列数=列数 if 列数>=合并['c']+合并['cs'] else 合并['c']+合并['cs']
        if 标签!='c':
            continue
        地址=节点.get('r') or 'A1'
        r=行号(地址)
        c=列号(地址)
        行数=行数 if 行数>=r+1 else r+1
        列数=列数 if 列数>=c+1 else c+1
        if 行数*列数>上限['maxCells']:
            raise 表格预览错误('tooLarge')
        类型=节点.get('t')
        公式=None
        值=None
        for 子 in 节点:
            子标=子.tag.rsplit('}',1)[-1]
            if 子标=='f':
                公式=子.text
            if 子标=='v':
                值=子.text
        格={}
        if 公式 is not None and 公式!='':
            格['f']='='+公式
            if 值 is None:
                缺+=1
        if 类型=='s' and 值 is not None:
            try:
                格['v']=共享[int(值)]
            except (ValueError,IndexError):
                格['v']=值
        elif 类型=='b':
            格['v']=值=='1'
        elif 值 is not None:
            try:
                if '.' in 值 or 'e' in 值.lower():
                    格['v']=float(值)
                else:
                    格['v']=int(值)
            except ValueError:
                格['v']=值
        单元格.append({'r':r,'c':c,'v':格式化单元格(格,'General')})
    return 行数,列数,单元格,配置,缺
