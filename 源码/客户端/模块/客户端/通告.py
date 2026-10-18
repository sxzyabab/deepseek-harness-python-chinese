__all__=['通知订阅者','可观察快照','登记握手窗口','取握手窗口']#仅中文公开名

握手窗口=None#这次握手传进来的窗口


def 登记握手窗口(窗口):
    '记下传进来的窗口。后面不许再自己创建'
    global 握手窗口
    握手窗口=窗口


def 取握手窗口():
    '返回这次握手传进来的窗口'
    if 握手窗口 is None:#还没传
        raise RuntimeError('窗口还没有传进来')#不许自己创建
    return 握手窗口


class 可观察快照:
    '页面钩子读的快照源。getSnapshot 与 subscribe 是协议名'
    def __init__(自身,读取,订阅):
        '读取返回当前值。订阅登记监听并返回退订函数'
        自身.读取=读取#读当前值
        自身.订阅=订阅#登记监听

    def getSnapshot(自身):
        '当前快照'
        return 自身.读取()#当前值

    def subscribe(自身,监听器):
        '订阅变化'
        return 自身.订阅(监听器)#退订函数


def 通知订阅者(监听器集,标签):
    '逐个调用。一个订阅者抛错不能跳过其余'
    for 监听器 in list(监听器集):#先拷再派发
        try:#隔离一个订阅者
            监听器()#通知
        except Exception as 错误:#订阅者失败
            取握手窗口().console.error('client-modules: '+标签+' subscriber failed',错误)#页面控制台
