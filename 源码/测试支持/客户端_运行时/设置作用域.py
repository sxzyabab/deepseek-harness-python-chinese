"""客户端设置作用域接缝的测试替身。

对齐上游 `client-runtime/src/settings-scope.ts`。公开面仅中文名。
"""
__all__=['桩设置作用域']#仅中文公开名

class 间谍函数:#简单 spy 可调用（对齐 vitest vi.fn）
    """记录调用并可选委托实现。"""

    def __init__(自身,实现=None):#构造
        """记下可选实现。"""
        自身.实现=实现#委托实现
        自身.calls=[]#调用记录
        自身.call_count=0#调用次数

    def __call__(自身,*位置参数,**关键字参数):#调用
        """记录并委托。"""
        自身.calls.append({'args':位置参数,'kwargs':关键字参数})#记录
        自身.call_count+=1#计数
        if 自身.实现 is not None:#有实现
            return 自身.实现(*位置参数,**关键字参数)#委托
        return None#默认空

    def mockClear(自身):#清空记录
        """清空调用记录。"""
        自身.calls.clear()#清空
        自身.call_count=0#归零

def 桩设置作用域():#构建桩作用域
    """为服务规格构建内存设置作用域。"""
    快照={#初始快照
        'status':'loading','value':None,'base':None,'user':None,#加载态
        'revision':None,'writable':False,'mode':'host',#修订与模式
    }#初始加载快照
    监听者=set()#订阅者
    def 空成功():#立即成功
        """立即解决的空写。"""
        return None#成功
    设置=间谍函数(lambda *_位置,**_关键字:空成功())#set 桩
    变更=间谍函数(lambda *_位置,**_关键字:空成功())#mutate 桩
    清除=间谍函数(lambda *_位置,**_关键字:空成功())#unset 桩
    def 订阅(监听):#订阅
        """登记监听器。"""
        监听者.add(监听)#订阅
        def 退订():#退订
            """取消。"""
            监听者.discard(监听)#退订
        return 退订#退订器
    def 发布(下一批):#发布
        """替换快照一部分并通知。"""
        快照.update(下一批)#合并发布
        for 监听 in list(监听者):#通知
            监听()#触发
    return {#返回句柄
        'scope':{#作用域面
            'getSnapshot':lambda:快照,#读快照
            'subscribe':订阅,#订阅
            'mutate':变更,#变更
            'set':设置,#写入
            'unset':清除,#清除
        },#scope 结束
        'set':设置,#暴露 set spy
        'mutate':变更,#暴露 mutate spy
        'unset':清除,#暴露 unset spy
        'listenerCount':lambda:len(监听者),#计数
        'publish':发布,#发布
    }#返回结束

stubSettingsScope=桩设置作用域#上游名
