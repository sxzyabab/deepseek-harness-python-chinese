__all__=['读持久会话']

def 读持久会话(持久化,标识,信号):
    '经短命读句柄读取已存会话的头与完整事件日志，关闭句柄后兑现。返回期约'
    def 读取事件(句柄):#句柄打开后
        '读完整事件日志，无论成败都关闭句柄'
        def 汇总(事件表):#事件读完
            '连同句柄上的头与继承事件数一起交出'
            return {
                'header':句柄.header,
                'inheritedEventCount':句柄.inheritedEventCount,
                'events':事件表,
            }
        return 句柄.read(0,None,{'signal':信号}).然后(汇总).最终(句柄.close)#读取失败也要关闭句柄
    return 持久化.open(标识,'read',{'signal':信号}).然后(读取事件)#先打开读句柄
