包名='@deepseek-ai/dsh-subagent'#本包的不变量所有权名
名称='subagent-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 校验运行结束(开始,结束,失败):
    """断言终态生命周期载荷与其启动身份一致：提供方、子 id、本地性三者必须同对。事件为 dict。"""
    if (开始['provider']!=结束['provider'] or 开始['id']!=结束['id'] or 开始['local']!=结束['local']):#身份分叉
        失败('subagent/end identity diverges from subagent/start for run '+repr(结束['runId']))#身份不一致

def 安装(上下文对象,失败):
    """在 dispatch 预检、正式事件提交两阶段跟踪提供方集合与未结束跑。"""
    提供方集合=set(上下文对象.subagents.列出())#当前已登记提供方名
    跑表={}#未结束跑的 start 载荷，键为 runId
    暂存提供方=set()#dispatch 已暂存的新增提供方对象 id
    暂存移除=set()#dispatch 已暂存的移除名
    暂存开始=set()#dispatch 已暂存的 start 对象 id
    暂存结束=set()#dispatch 已暂存的 end 对象 id

    def 派发检查(_模式,事件名,参数,*其余):
        """在正式提交前暂存并预检子智能体事件；非法则经失败回调大声失败。"""
        if 事件名=='subagent/provider-added':#新增提供方
            提供方=参数[0]#载荷是提供方对象
            名=提供方.name#提供方名
            if len(名)==0:#名非空
                失败('subagent provider names must be non-empty')#名非空
            if 名 in 提供方集合:#禁止重复名
                失败('subagent/provider-added repeated '+repr(名))#禁止重复名
            暂存提供方.add(id(提供方))#暂存以待正式事件提交
            return#本事件处理完
        if 事件名=='subagent/provider-removed':#移除提供方
            提供方名=参数[0]#载荷是名字
            if 提供方名 not in 提供方集合:#必须已知
                失败('subagent/provider-removed names unknown provider '+repr(提供方名))#必须已知
            暂存移除.add(提供方名)#暂存移除
            return#本事件处理完
        if 事件名=='subagent/start':#跑开始
            载荷=参数[0]#start 载荷
            if (len(载荷['provider'])==0 or len(str(载荷['runId']))==0 or len(str(载荷['id']))==0):#身份必须非空
                失败('subagent/start provider, runId, and child id must be non-empty')#身份必须非空
            跑键=载荷['runId']#跑 id
            if 跑键 in 跑表:#禁止重复 runId
                失败('subagent/start repeated run id '+repr(跑键))#禁止重复 runId
            暂存开始.add(id(载荷))#暂存 start
            return#本事件处理完
        if 事件名!='subagent/end':#其余事件忽略
            return#忽略
        载荷=参数[0]#end 载荷
        if 载荷['runId'] not in 跑表:#必须先有 start
            失败('subagent/end has no matching subagent/start for run '+repr(载荷['runId']))#必须先有 start
        校验运行结束(跑表[载荷['runId']],载荷,失败)#校验身份一致
        暂存结束.add(id(载荷))#暂存 end

    上下文对象.监听('internal/dispatch',派发检查,{'全局':True})#全局监听 dispatch

    def 提交新增(提供方):
        """仅提交经 dispatch 暂存过的新增；旁路 emit 忽略。"""
        if id(提供方) not in 暂存提供方:#未经 dispatch 暂存则忽略
            return#忽略
        暂存提供方.discard(id(提供方))#清掉暂存
        提供方集合.add(提供方.name)#记入注册表

    def 提交移除(提供方名):
        """仅提交经 dispatch 暂存过的移除。"""
        if 提供方名 not in 暂存移除:#未经 dispatch 暂存则忽略
            return#忽略
        暂存移除.discard(提供方名)#清掉暂存
        提供方集合.discard(提供方名)#移出注册表

    def 提交开始(载荷):
        """把经预检的 start 记入未结束跑表。"""
        if id(载荷) not in 暂存开始:#未经 dispatch 暂存则忽略
            return#忽略
        暂存开始.discard(id(载荷))#清掉暂存
        跑表[载荷['runId']]=载荷#记入未结束跑

    def 提交结束(载荷):
        """配对成功后移出未结束跑。"""
        if id(载荷) not in 暂存结束:#未经 dispatch 暂存则忽略
            return#忽略
        暂存结束.discard(id(载荷))#清掉暂存
        跑表.pop(载荷['runId'],None)#移出未结束跑

    上下文对象.监听('subagent/provider-added',提交新增,{'全局':True})#全局监听
    上下文对象.监听('subagent/provider-removed',提交移除,{'全局':True})#全局监听
    上下文对象.监听('subagent/start',提交开始,{'全局':True})#全局监听
    上下文对象.监听('subagent/end',提交结束,{'全局':True})#全局监听

安装.inject=['subagents']#invariants 登记约定读 inject 槽

def 应用(上下文对象):
    """注册子智能体不变量配套，返回拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
