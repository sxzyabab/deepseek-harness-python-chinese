"""本包拥有的子智能体注册表与生命周期不变量。公开面仅中文名；Cordis 协议槽不进入 `__all__`。"""
from concurrent.futures import Future as _原生Future#单次操作结果

包名='@deepseek-ai/dsh-subagent'#本包的不变量所有权名
名称='subagent-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖声明槽

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 校验跑结束(开始,结束,失败):#校验 start/end 配对
    """断言终态生命周期载荷与其启动身份一致：提供方、子 id、本地性三者必须同对。"""
    if (取字段(开始,'provider')!=取字段(结束,'provider')#提供方分叉
        or 取字段(开始,'id')!=取字段(结束,'id')#子 id 分叉
        or 取字段(开始,'local')!=取字段(结束,'local')):#本地性分叉
        失败('subagent/end identity diverges from subagent/start for run '+repr(取字段(结束,'runId')))#身份不一致

def 安装(上下文对象,失败):#安装提供方注册表与 start/end 配对检查
    """在 dispatch 预检、正式事件提交两阶段跟踪提供方集合与未结束跑。"""
    提供方们=set(上下文对象.subagents.列出())#当前已登记提供方名
    跑们={}#未结束跑的 start 信息，键为 runId
    暂存提供方=set()#dispatch 已暂存的新增提供方对象 id
    暂存移除=set()#dispatch 已暂存的移除名
    暂存开始=set()#dispatch 已暂存的 start 对象 id
    暂存结束=set()#dispatch 已暂存的 end 对象 id

    def 派发检查(_模式,事件名,参数,*其余):#在派发时暂存并预检
        """在正式提交前暂存并预检子智能体事件；非法则经失败回调大声失败。"""
        if 事件名=='subagent/provider-added':#新增提供方
            提供方=参数[0]#载荷是提供方
            名=取字段(提供方,'name') or 取字段(提供方,'名称') or ''#提供方名
            if len(名)==0:#名非空
                失败('subagent provider names must be non-empty')#名非空
            if 名 in 提供方们:#禁止重复名
                失败('subagent/provider-added repeated '+repr(名))#禁止重复名
            暂存提供方.add(id(提供方))#暂存以待正式事件提交
            return#本事件处理完
        if 事件名=='subagent/provider-removed':#移除提供方
            提供方名=参数[0]#载荷是名字
            if 提供方名 not in 提供方们:#必须已知
                失败('subagent/provider-removed names unknown provider '+repr(提供方名))#必须已知
            暂存移除.add(提供方名)#暂存移除
            return#本事件处理完
        if 事件名=='subagent/start':#跑开始
            信息=参数[0]#start 载荷
            # 提供方可用性是准入时关系。已发布的一次性跑可以活过提供方移除，冷恢复的 Activation 记下初始提供方名而不经它派发。
            if (len(取字段(信息,'provider') or '')==0#提供方空
                or len(str(取字段(信息,'runId') or ''))==0#跑 id 空
                or len(str(取字段(信息,'id') or ''))==0):#子 id 空
                失败('subagent/start provider, runId, and child id must be non-empty')#身份必须非空
            跑键=取字段(信息,'runId')#跑 id
            if 跑键 in 跑们:#禁止重复 runId
                失败('subagent/start repeated run id '+repr(跑键))#禁止重复 runId
            暂存开始.add(id(信息))#暂存 start
            return#本事件处理完
        if 事件名!='subagent/end':#其余事件忽略
            return#忽略
        信息=参数[0]#end 载荷
        开始=跑们.get(取字段(信息,'runId'))#配对的 start
        if 开始 is None:#必须先有 start
            失败('subagent/end has no matching subagent/start for run '+repr(取字段(信息,'runId')))#必须先有 start
        校验跑结束(开始,信息,失败)#校验身份一致
        暂存结束.add(id(信息))#暂存 end

    上下文对象.on('internal/dispatch',派发检查,{'global':True})#全局监听 dispatch

    def 提交新增(提供方):#提交新增提供方
        """仅提交经 dispatch 暂存过的新增；旁路 emit 忽略。"""
        if id(提供方) not in 暂存提供方:#未经 dispatch 暂存则忽略
            return#忽略
        暂存提供方.discard(id(提供方))#清掉暂存
        提供方们.add(取字段(提供方,'name') or 取字段(提供方,'名称'))#记入注册表

    def 提交移除(提供方名):#提交移除提供方
        """仅提交经 dispatch 暂存过的移除。"""
        if 提供方名 not in 暂存移除:#未经 dispatch 暂存则忽略
            return#忽略
        暂存移除.discard(提供方名)#清掉暂存
        提供方们.discard(提供方名)#移出注册表

    def 提交开始(信息):#提交跑开始
        """把经预检的 start 记入未结束跑表。"""
        if id(信息) not in 暂存开始:#未经 dispatch 暂存则忽略
            return#忽略
        暂存开始.discard(id(信息))#清掉暂存
        跑们[取字段(信息,'runId')]=信息#记入未结束跑

    def 提交结束(信息):#提交跑结束
        """配对成功后移出未结束跑。"""
        if id(信息) not in 暂存结束:#未经 dispatch 暂存则忽略
            return#忽略
        暂存结束.discard(id(信息))#清掉暂存
        跑们.pop(取字段(信息,'runId'),None)#移出未结束跑

    上下文对象.on('subagent/provider-added',提交新增,{'global':True})#全局监听
    上下文对象.on('subagent/provider-removed',提交移除,{'global':True})#全局监听
    上下文对象.on('subagent/start',提交开始,{'global':True})#全局监听
    上下文对象.on('subagent/end',提交结束,{'global':True})#全局监听

# 安装器还依赖 subagents：上游 Object.assign(install, { inject: ['subagents'] })
安装.注入=['subagents']#中文依赖声明
安装.inject=安装.注入#invariants 登记约定读 inject 槽

def 应用(上下文对象):#应用不变量配套插件
    """注册子智能体不变量配套，返回已安装注册的 disposer（包装为已兑现任务）。"""
    class 操作任务:#单次异步结果
        def __init__(自身):#构造已决任务
            自身._future=_原生Future()#底层 Future
            自身._future.set_result(None)#占位
        def 兑现(自身,值=None):#成功结算
            if not 自身._future.done():#尚未结算
                自身._future.set_result(值)#写入结果
            return 值#返回兑现值
        def wait(自身,超时=None):#阻塞等待
            return 自身._future.result(timeout=超时)#取结果或抛错
        def 等待(自身,超时=None):#兼容外来调用
            return 自身.wait(超时)#转发
    拆除器=上下文对象.invariants.register(包名,安装)#注册本包不变量
    任务=操作任务()#新任务
    任务.兑现(拆除器)#立刻兑现拆除器
    return 任务#已决议任务

apply=应用#Cordis 插件入口槽
