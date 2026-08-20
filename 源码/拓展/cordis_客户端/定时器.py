"""Cordis 定时器服务的浏览器契约与调度算法面。

对齐上游 `cordis-client-runner/src/client/timer.ts`。公开面仅中文名。
无法在本树执行：globalThis.setTimeout/setInterval 与 Fiber effect 挂接。
本模块落盘服务键、混入助手、以及用可注入时钟实现的 timeout/interval/throttle/debounce 算法。
"""

__all__=[#仅中文公开名
    '服务键','混入助手','说明','默认时钟','客户端定时器服务','安装客户端定时器',
]#公开面结束

说明='真实 ClientTimerService 需浏览器定时器 API 与 cordis Service/mixin；本类以可注入时钟跑同一调度算法。'#说明

服务键='timer'#ctx.timer
混入助手=('timeout','interval','throttle','debounce','setTimeout','setInterval')#混入名

def 默认时钟():#无浏览器时的同步记账时钟
    """返回 setTimeout/clearTimeout/setInterval/clearInterval；不睡真实时间，仅登记句柄。"""
    下一= {'n':1}#句柄序号
    挂起={}#id → 条目
    def 设超时(回调,延迟,*位置):#一次
        """登记；不自动触发。"""
        标识=下一['n']#id
        下一['n']=标识+1#增
        挂起[标识]={'kind':'timeout','fn':回调,'delay':延迟,'args':位置}#记
        return 标识#句柄
    def 清超时(标识):#清一次
        """拿掉。"""
        挂起.pop(标识,None)#删
    def 设间隔(回调,延迟,*位置):#反复
        """登记。"""
        标识=下一['n']#id
        下一['n']=标识+1#增
        挂起[标识]={'kind':'interval','fn':回调,'delay':延迟,'args':位置}#记
        return 标识#句柄
    def 清间隔(标识):#清反复
        """拿掉。"""
        挂起.pop(标识,None)#删
    return {#时钟
        'setTimeout':设超时,'clearTimeout':清超时,
        'setInterval':设间隔,'clearInterval':清间隔,
        'pending':挂起,#测试可见
    }#结束

class 客户端定时器服务:#ClientTimerService 算法面
    """timeout/interval/throttle/debounce；经 effect 挂接时由上下文提供拆除。"""
    def __init__(自身,上下文=None,时钟=None):#构造
        """可选 ctx.effect 与可注入时钟。"""
        自身.上下文=上下文#ctx
        自身.时钟=时钟 or 默认时钟()#时钟

    def _挂effect(自身,标签,拆除体):#Fiber 挂接
        """有 effect 则登记；否则返回拆除体本身。"""
        if 自身.上下文 is not None and hasattr(自身.上下文,'effect'):#有
            return 自身.上下文.effect(lambda:拆除体,标签)#挂
        return 拆除体#裸

    def setTimeout(自身,回调,延迟):#兼容别名
        """转发 timeout 回调形。"""
        return 自身.timeout(回调,延迟)#转发

    def setInterval(自身,回调,延迟):#兼容别名
        """转发 interval 回调形。"""
        return 自身.interval(回调,延迟)#转发

    def timeout(自身,*位置参数):#延迟一次：回调形或等待形
        """`(callback, delay)` → 拆除器；`(delay,)` → 承诺结构（无真实睡）。"""
        参数=list(位置参数)#拷
        回调=参数.pop(0) if 参数 and callable(参数[0]) else None#可选回调
        延迟=参数[0] if 参数 else 0#延迟
        if 回调 is not None:#回调形
            状态={'id':None,'done':False,'dispose':None}#态
            def 到期():#跑
                """对齐上游：先拆 effect，再跑回调。"""
                if 状态['done']:#已拆
                    return#停
                拆=状态.get('dispose')#拆除器
                if callable(拆):#有
                    拆()#先拆（标 done + 清定时器）
                回调()#再跑
            def 拆除体():#清
                """清定时器。"""
                状态['done']=True#标
                自身.时钟['clearTimeout'](状态['id'])#清
            拆除=自身._挂effect('ctx.timeout()',拆除体)#挂
            状态['dispose']=拆除#供到期回调先拆
            状态['id']=自身.时钟['setTimeout'](到期,延迟)#排
            return 拆除#拆除器
        # 等待形：无真实异步，返回可查询结构
        状态={'id':None,'resolved':False,'rejected':False,'reason':None}#态
        def 兑现():#到期
            """标兑现。"""
            状态['resolved']=True#兑
        def 拆除体():#拆
            """拒并清。"""
            自身.时钟['clearTimeout'](状态['id'])#清
            if not 状态['resolved']:#未兑
                状态['rejected']=True#拒
                状态['reason']=Exception('Context has been disposed')#因
        拆除=自身._挂effect('ctx.timeout()',拆除体)#挂
        状态['id']=自身.时钟['setTimeout'](兑现,延迟)#排
        状态['dispose']=拆除#句柄
        return 状态#承诺结构

    def interval(自身,*位置参数):#反复：回调形或迭代器形
        """`(callback, delay)` → 拆除器；`(delay,)` → 异步迭代器结构。"""
        参数=list(位置参数)#拷
        回调=参数.pop(0) if 参数 and callable(参数[0]) else None#可选
        延迟=参数[0] if 参数 else 0#间隔
        if 回调 is not None:#回调形
            状态={'id':None}#态
            def 拆除体():#清
                """清间隔。"""
                自身.时钟['clearInterval'](状态['id'])#清
            拆除=自身._挂effect('ctx.interval()',拆除体)#挂
            状态['id']=自身.时钟['setInterval'](回调,延迟)#排
            return 拆除#拆除器
        结束= {'kind':None,'value':None,'reason':None}#结束态
        下一任务= {'resolve':None,'reject':None}#挂起 next
        状态={'id':None}#句柄
        def 滴答():#唤醒
            """兑现挂起 next。"""
            兑=下一任务.get('resolve')#兑
            if callable(兑):#有
                下一任务['resolve']=None#清
                下一任务['reject']=None#清
                兑({'done':False,'value':None})#滴答
        def 拆除体():#拆
            """拒挂起 next。"""
            自身.时钟['clearInterval'](状态['id'])#清
            if 结束['kind'] is not None:#已结束
                return#停
            结束['kind']='throw'#记
            结束['reason']=Exception('Context has been disposed')#因
            拒=下一任务.get('reject')#拒
            if callable(拒):#有
                下一任务['resolve']=None#清
                下一任务['reject']=None#清
                拒(结束['reason'])#拒
        拆除=自身._挂effect('ctx.interval()',拆除体)#挂
        状态['id']=自身.时钟['setInterval'](滴答,延迟)#排
        def next_():#下一滴答
            """等下一滴答或结束。"""
            if 结束['kind'] is None:#还在跑
                盒={'result':None}#盒
                def 兑(值):#兑
                    """写入。"""
                    盒['result']=('ok',值)#兑
                def 拒(因):#拒
                    """写入。"""
                    盒['result']=('err',因)#拒
                下一任务['resolve']=兑#挂
                下一任务['reject']=拒#挂
                return 盒#待
            if 结束['kind']=='return':#已 return
                return {'done':True,'value':结束['value']}#完成
            raise 结束['reason']#已 throw
        def return_(值=None):#提前结束
            """记下 return 并拆。"""
            if 结束['kind'] is None:#未结束
                结束['kind']='return'#记
                结束['value']=值#值
            兑=下一任务.get('resolve')#兑
            if callable(兑):#有
                下一任务['resolve']=None#清
                下一任务['reject']=None#清
                兑({'done':True,'value':值})#醒
            拆除()#拆
            return {'done':True,'value':值}#完成
        def throw_(因):#注入错误
            """记下 throw 并拆。"""
            if 结束['kind'] is None:#未结束
                结束['kind']='throw'#记
                结束['reason']=因#因
            拒=下一任务.get('reject')#拒
            if callable(拒):#有
                下一任务['resolve']=None#清
                下一任务['reject']=None#清
                拒(因)#拒
            拆除()#拆
            return {'done':True,'value':None}#协议
        return {'next':next_,'return':return_,'throw':throw_,'dispose':拆除}#迭代器结构

    def _安排(自身,标签,触发,初始已拆=False):#节流/防抖共用
        """返回带 dispose 的包装函数。"""
        态={'timer':None,'disposed':初始已拆}#态
        def 拆除体():#拆
            """标拆并清。"""
            态['disposed']=True#标
            自身.时钟['clearTimeout'](态['timer'])#清
        拆除=自身._挂effect(标签,拆除体)#挂
        def 包装(*位置):#包装
            """取消上次再按策略排。"""
            自身.时钟['clearTimeout'](态['timer'])#取消
            态['timer']=触发(位置,态['disposed'])#安排
        包装.dispose=拆除#提前拆除
        return 包装#函数

    def throttle(自身,回调,延迟,无尾随=False):#节流
        """最小间隔；noTrailing 抑制尾随。"""
        import time as 时间#时刻
        上次={'-':float('-inf')}#上次执行
        def 执行(*位置):#真正执行
            """记下时刻。"""
            上次['-']=时间.time()*1000#毫秒
            回调(*位置)#调用
        def 触发(位置,已拆):#安排
            """立刻或延迟。"""
            剩余=延迟-(时间.time()*1000-上次['-'])#剩
            if 剩余<=0:#已过
                执行(*位置)#立刻
                return None#无挂起
            if not 已拆:#尾随
                return 自身.时钟['setTimeout'](lambda:执行(*位置),剩余)#延迟
            return None#抑尾随
        return 自身._安排('ctx.throttle()',触发,无尾随)#包装

    def debounce(自身,回调,延迟):#防抖
        """安静期后再跑。"""
        def 触发(位置,已拆):#安排
            """已拆则不再排。"""
            if 已拆:#已拆
                return None#停
            return 自身.时钟['setTimeout'](lambda:回调(*位置),延迟)#排
        return 自身._安排('ctx.debounce()',触发)#包装

def 安装客户端定时器(上下文,时钟=None):#provideClientTimer
    """构造服务、provide/mixin；返回服务实例。"""
    服务=客户端定时器服务(上下文,时钟)#实例
    if 上下文 is not None and hasattr(上下文,'provide'):#有
        上下文.provide(服务键,服务)#挂
    if 上下文 is not None and hasattr(上下文,'mixin'):#有
        上下文.mixin(服务键,list(混入助手))#混入
    return 服务#实例
