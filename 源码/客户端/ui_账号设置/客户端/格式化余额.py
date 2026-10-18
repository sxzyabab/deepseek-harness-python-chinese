'按平台网页的两位小数和不足一分规则显示余额'
from ...模块.客户端.通告 import 取握手窗口
from decimal import Decimal,ROUND_DOWN,ROUND_HALF_UP

__all__=['格式化余额','加逗号']

def 加逗号(文本):
    '整数部分用浏览器当前语言的分组'
    段=文本.split('.')
    整数=段[0]
    小数=段[1]
    窗口=取握手窗口()
    分组=窗口.Number(int(整数)).toLocaleString()
    return str(分组)+'.'+小数

def 格式化余额(金额,符号):
    '带符号的余额。零是 0.00，不足一分按小于或最小一分显示'
    值=Decimal(金额)
    分=Decimal('0.01')
    if 值==0:
        return 符号+'0.00'
    if 值<0:
        if 值>Decimal('-0.01'):
            尾='0.01'
        else:
            正=abs(值).quantize(分,rounding=ROUND_HALF_UP)
            尾=加逗号(format(正,'f'))
        return '-'+符号+尾
    if 值<分:
        return '<'+符号+'0.01'
    舍=值.quantize(分,rounding=ROUND_DOWN)
    return 符号+加逗号(format(舍,'f'))
