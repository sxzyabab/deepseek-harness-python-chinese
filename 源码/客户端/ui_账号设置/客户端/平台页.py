'账号功能共用的一个原生平台页请求'
from ...存储 import 创建快照存储

__all__=['创建平台页']

def 创建平台页():
    '设置页、额度通知和桌面充值都向这一条通道要页面'
    存储=创建快照存储(None)
    业主={'回调':None,'令牌':None}
    def 取快照():
        '当前请求。没有页面时是 null'
        return 存储.getSnapshot()
    def 订阅(监听):
        '请求变化后通知'
        return 存储.subscribe(监听)
    def 打开(页,关闭时):
        '新请求先装上，再通知被换掉的业主。旧的放开不能关掉新的'
        先前=业主['回调']
        自己={}
        业主['令牌']=自己
        业主['回调']=关闭时
        存储.set({'page':页})
        if 先前 is not None:
            先前('superseded')
        def 放开():
            '只清掉仍属于这次请求的页面'
            if 业主['令牌'] is not 自己:
                return
            业主['令牌']=None
            业主['回调']=None
            存储.set(None)
        return 放开
    def 关闭():
        '用户返回。清掉当前请求并通知业主一次'
        if 存储.getSnapshot() is None:
            return
        将退=业主['回调']
        业主['令牌']=None
        业主['回调']=None
        存储.set(None)
        if 将退 is not None:
            将退('returned')
    def 拆除():
        '插件卸下时丢掉请求，不通知业主'
        业主['令牌']=None
        业主['回调']=None
        if 存储.getSnapshot() is None:
            return
        存储.set(None)
    return {
        'getSnapshot':取快照,
        'subscribe':订阅,
        'open':打开,
        'close':关闭,
        'dispose':拆除,
    }
