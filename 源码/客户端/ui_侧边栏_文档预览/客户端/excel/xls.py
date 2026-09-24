from .错误 import 表格预览错误
from .模型 import 格式化单元格,初始选区

__all__=['转换xls','映射xls工作簿']

_复合=(0xd0,0xcf,0x11,0xe0,0xa1,0xb1,0x1a,0xe1)
_biff版本=(0x00,0x02,0x04,0x08)

def 转换xls(字节,上限):
    """拒绝改名文本或 HTML；无 BIFF 表时按无效失败。"""
    复合=len(字节)>=8 and all(字节[下标]==_复合[下标] for 下标 in range(8))
    biff版本=字节[1] if len(字节)>1 else None
    biff=len(字节)>0 and 字节[0]==0x09 and biff版本 in _biff版本
    if not 复合 and not biff:
        raise 表格预览错误('invalid')
    raise 表格预览错误('invalid')

def 映射xls工作簿(工作簿,上限):
    """把已解析的遗留工作簿映到显示格。"""
    面积=0
    缺结果=0
    名表=工作簿['SheetNames']
    簿元=工作簿.get('Workbook') if isinstance(工作簿,dict) else None
    表元=None if not isinstance(簿元,dict) else 簿元.get('Sheets')
    可见表=[]
    序=0
    for _名 in 名表:
        隐=False
        if isinstance(表元,list) and 序<len(表元) and isinstance(表元[序],dict):
            隐=bool(表元[序].get('Hidden'))
        可见表.append(not 隐)
        序+=1
    活动=-1
    下=0
    for 可见 in 可见表:
        if 可见:
            活动=下
            break
        下+=1
    if 活动<0:
        raise 表格预览错误('invalid')
    工作表=[]
    序=0
    源表=工作簿['Sheets']
    for 名 in 名表:
        源=源表.get(名)
        if 源 is None:
            raise 表格预览错误('invalid')
        引用=源.get('!ref') or 'A1'
        行,列=_维(引用)
        for 合并 in 源.get('!merges') or ():
            行=行 if 行>合并['e']['r'] else 合并['e']['r']
            列=列 if 列>合并['e']['c'] else 合并['e']['c']
        行数=行+1
        列数=列+1
        面积+=行数*列数
        if 面积>上限['maxCells']:
            raise 表格预览错误('tooLarge')
        配置={'merge':{},'rowlen':{},'columnlen':{},'rowhidden':{},'colhidden':{}}
        格表={}
        for 地址,单元格 in 源.items():
            if not isinstance(地址,str) or 地址.startswith('!'):
                continue
            v={}
            if isinstance(单元格,dict) and 单元格.get('f') is not None:
                v['f']='='+str(单元格['f'])
            if isinstance(单元格,dict) and 'v' in 单元格:
                v['v']=单元格['v']
            if v.get('f') is not None and 'v' not in v:
                缺结果+=1
            r,c=_格址(地址)
            格表[str(r)+'_'+str(c)]={'r':r,'c':c,'v':格式化单元格(v,str(单元格.get('z') if isinstance(单元格,dict) else 'General'))}
        显示=可见表[序] is True
        状态=1 if 序==活动 else 0
        工作表.append({
            'id':str(序+1),'name':名,'order':序,'status':状态,'hide':0 if 显示 else 1,
            'row':行数,'column':列数,'config':配置,'celldata':list(格表.values()),
            'luckysheet_select_save':初始选区(配置),
        })
        序+=1
    return {'sheets':工作表,'missingResults':缺结果,'unsupportedFeatures':[]}

def _维(引用):
    段=引用.split(':')
    止=段[-1]
    return _格址(止)

def _格址(地址):
    列=0
    行=0
    for 字 in 地址:
        if 'A'<=字<='Z':
            列=列*26+(ord(字)-64)
        elif '0'<=字<='9':
            行=行*10+int(字)
    return 行-1,列-1
