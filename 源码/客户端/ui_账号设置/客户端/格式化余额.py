from decimal import Decimal,ROUND_DOWN,ROUND_HALF_UP

__all__=['格式化余额']

def 加千分位(文本):
    """整数部分按千分位分组，小数部分原样接回。"""
    整数,小数=文本.split('.')
    return f'{int(整数):,}.{小数}'

def 格式化余额(金额,符号):
    """按 Platform Web 两位小数与不足一分的显示规则格式化余额。"""
    值=Decimal(金额)
    if 值==0:
        return 符号+'0.00'
    if 值<0:
        绝对=值.copy_abs()
        展示='0.01' if 值>Decimal('-0.01') else 加千分位(format(绝对.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP),'f'))
        return '-'+符号+展示
    if 值<Decimal('0.01'):
        return '<'+符号+'0.01'
    量化=值.quantize(Decimal('0.01'),rounding=ROUND_DOWN)
    return 符号+加千分位(format(量化,'f'))
