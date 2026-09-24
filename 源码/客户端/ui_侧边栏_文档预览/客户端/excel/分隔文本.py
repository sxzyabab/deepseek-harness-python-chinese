import csv,io
from .错误 import 表格预览错误
from .模型 import 格式化单元格,初始选区

__all__=['转换分隔文本']

def 转换分隔文本(字节,格式,上限):
    """按字面保留每个字段，不做类型推断。"""
    if len(字节)>=2 and 字节[0]==0xff and 字节[1]==0xfe:
        编码='utf-16-le'
    elif len(字节)>=2 and 字节[0]==0xfe and 字节[1]==0xff:
        编码='utf-16-be'
    else:
        编码='utf-8'
    try:
        文本=字节.decode(编码)
    except UnicodeDecodeError as 错误:
        raise 表格预览错误('encoding') from 错误
    分隔=',' if 格式=='csv' else '\t'
    单元格数据=[]
    行=0
    列=1
    读=csv.reader(io.StringIO(文本),delimiter=分隔)
    for 字段表 in 读:
        行+=1
        列=列 if 列>=len(字段表) else len(字段表)
        if 行*列>上限['maxCells']:
            raise 表格预览错误('tooLarge')
        下标=0
        for 值 in 字段表:
            单元格数据.append({'r':行-1,'c':下标,'v':格式化单元格({'v':值},'@')})
            下标+=1
    return {
        'sheets':[{
            'id':'1','name':格式.upper(),'order':0,'status':1,'hide':0,
            'row':1 if 行<1 else 行,'column':列,'celldata':单元格数据,'config':{},
            'luckysheet_select_save':初始选区({}),
        }],
        'missingResults':0,
        'unsupportedFeatures':[],
    }
