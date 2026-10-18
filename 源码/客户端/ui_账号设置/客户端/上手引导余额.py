'上手引导把充值余额和赠金都算进可用额度'
from decimal import Decimal

__all__=['有上手引导额度']

def 有上手引导额度(余额):
    '还在查询时不当成零。任一钱包大于零即有额度'
    if isinstance(余额,dict) is False or 余额.get('status')!='ready':
        return False
    钱包=list(余额.get('value') or [])
    钱包.extend(余额.get('bonusWallets') or [])
    for 项 in 钱包:
        if Decimal(项['balance'])>0:
            return True
    return False
