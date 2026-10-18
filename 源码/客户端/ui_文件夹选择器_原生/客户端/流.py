__all__=['原生目录流']

class 原生目录流:
    '无渲染的原生目录流。open 上升沿挑一次，结果交给 onPicked、onCancel 或 onError。不画页面'
    def __init__(自身):
        '武装旗起始未武装，存活旗为仍挂着。构造时不打开选择器'
        自身.属性=None#最新合成 props
        自身.已武装=False#这一轮 open 是否已经挑过
        自身.存活=True#卸下之后为假

    def 卸下(自身):
        '挂载卸下后，还没回来的结算不再调用主人'
        自身.存活=False#标死

    def __call__(自身,属性):
        '记下最新 props，并按 open 边沿决定是否打开选择器。返回 None'
        自身.属性=属性#回调始终走最新主人
        打开=属性['open']#主人是否请求挑选
        # 上升沿才挑。同一轮 open 里重画或换 pick 都不另开
        if not 打开:#撤回或尚未打开
            自身.已武装=False#下一轮可以再武装
            return None#不挑
        if 自身.已武装:#同一轮已经挑过
            return None#不再开第二个选择器
        自身.已武装=True#这一轮只武装一次
        def 成功(路径):
            '字符串路径采纳，None 取消。占用者已卸则丢掉'
            if not 自身.存活:#已卸
                return#丢掉
            if 路径 is None:#主人取消
                自身.属性['onCancel']()#取消
                return#完
            自身.属性['onPicked'](路径)#采纳
        def 失败(原因):
            'Error 用 message，其余转成字符串。占用者已卸则丢掉'
            if not 自身.存活:#已卸
                return#丢掉
            if isinstance(原因,BaseException):#Python 异常当 Error
                消息=str(原因)#消息
            else:#页面对象或其它原因
                候选=getattr(原因,'message',None)#Error.message
                if isinstance(候选,str):#有消息
                    消息=候选#原文
                else:#没有消息
                    消息=str(原因)#转成字符串
            自身.属性['onError'](消息)#交给主人
        try:#打开选择器
            产出=属性['pick']()#同步值，或浏览器期约
        except Exception as 原因:#同步失败，对齐期约拒绝
            失败(原因)#交给主人
            return None#不再接 then
        if 产出 is not None:#可能是期约
            然后=getattr(产出,'then',None)#浏览器 Promise.then
            if callable(然后):#稍后才结算
                然后(成功,失败)#成败都走最新 props
                return None#选择器还开着
        成功(产出)#同步结果马上交
        return None#没有节点
