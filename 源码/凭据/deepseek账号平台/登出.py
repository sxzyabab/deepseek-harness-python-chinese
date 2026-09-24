import time
from ...工具.超时 import 已中止,截止
from .协议 import 登出账号,平台认证错误

__all__=['吊销账号']

def 吊销账号(来源,令牌,政策,信号,头):
    """后台吊销已从本地去掉的授予。"""
    尝试=0
    while 尝试<=政策['maxRetries']:
        if 已中止(信号):
            return
        if 尝试>0:
            延迟=政策['delayMs']*(2**(尝试-1))
            截止点=time.time()+延迟/1000.0
            while not 已中止(信号):
                剩余=截止点-time.time()
                if 剩余<=0:
                    break
                time.sleep(min(剩余,0.05))
            if 已中止(信号):
                return
        句柄=截止(信号,政策['requestTimeoutMs'],'account-logout')
        try:
            登出账号(来源,令牌,句柄.信号,头)
            return
        except 平台认证错误:
            pass
        finally:
            句柄.释放()
        尝试+=1
