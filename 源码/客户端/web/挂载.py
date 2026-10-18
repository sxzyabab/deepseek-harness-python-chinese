def 挂载客户端(上下文,容器):
    '经 uiRenderer 依赖纤程把渲染器挂进容器。服务还没有时，纤程先挂上，服务到了再装'
    def 安装(作用域,配置):
        '服务提供时安装挂载效应。配置由依赖启动传入，这个挂载不用'
        def 挂():
            '把渲染器挂到容器。返回值是卸下函数'
            return 作用域.uiRenderer['mount'](容器)#挂载
        作用域.副作用(挂,'web boot: application mount')#效应名保持上游原文
    纤程=上下文.依赖启动(['uiRenderer'],安装)#等 uiRenderer
    纤程.等待()#启动失败就抛出来
