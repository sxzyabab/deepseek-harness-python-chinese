__all__=['不支持特性表','初始选区','格式化单元格']

不支持特性表=('charts','images','shapes','conditionalFormatting')

def 初始选区(配置):
    """保留可寻址 A1 选区，含 A1 合并。"""
    合并=None
    if isinstance(配置,dict):
        并=配置.get('merge')
        if isinstance(并,dict):
            合并=并.get('0_0')
    行跨=1 if not isinstance(合并,dict) else 合并.get('rs',1)
    列跨=1 if not isinstance(合并,dict) else 合并.get('cs',1)
    return [{'row':[0,行跨-1],'column':[0,列跨-1],'row_focus':0,'column_focus':0}]

def 格式化单元格(单元格,数字格式):
    """套数字格式与默认对齐，不计算公式。"""
    值=单元格.get('v') if isinstance(单元格,dict) else None
    if 'ht' not in 单元格:
        if type(值) is bool:
            单元格['ht']=0
        elif type(值) in (int,float) and type(值) is not bool:
            单元格['ht']=2
        else:
            单元格['ht']=1
    if 'ct' not in 单元格:
        if type(值) is bool:
            类='b'
        elif type(值) in (int,float) and type(值) is not bool:
            类='n'
        else:
            类='s'
        单元格['ct']={'fa':数字格式,'t':类}
    if type(值) in (int,float) and type(值) is not bool:
        显示=值
    else:
        显示=值
    单元格['m']='' if 显示 is None else str(显示)
    return 单元格
