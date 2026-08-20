"""按会话的沙箱模式覆盖：会话日志即存储。运行时切换（UI 政策控件或测试场景）作为一条 `sandbox/mode` 事件记在它适用的会话上；`effective = fold(events) ?? 部署默认`，因此覆盖经回放挺过重启，两个会话永远看不到彼此的状态，也没有外部配置存储。该事件只进日志（`approval/*` 先例）：政策所有者把折叠投影进每次模型请求，强制工具报告操作特定的边界标记。执行经 `ctx.sandboxPolicy.resolve()` 遵守同一折叠——它把模式连同调用会话的工作区根盖到每次能力调用上，优先级弱于升级授予。

覆盖是每个强制家族（bash 与文件系统）共享的政策状态，因此放在政策包这里，而不是任一能力的 seam。

会话事件映射扩展（文档约定，对齐上游 SessionEventMap）：
`sandbox/mode`：会话的沙箱模式被切换——只进日志（像 `approval/*`；不是展示事件，不带 `surfaceOp`）：持久可回放，从不进模型文本记录。最后一条此类事件是会话的覆盖（生效沙盒模式）。`source: 'delegation'` 标记播种进子智能体的覆盖；缺失 source 是运行时切换。载荷字段：`mode`（SandboxMode）、可选 `source`（`'delegation'`）。
"""
沙盒模式表=('read-only','workspace-write','danger-full-access')#每一个 SandboxMode，供选项广告与对不受信任模式字符串的运行时校验

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 生效沙盒模式(事件们):#折叠会话覆盖
    """会话的沙箱模式覆盖：日志里最后一条 `sandbox/mode` 事件；会话从未切换过则为 None（调用方应用部署默认）。纯折叠——恢复不需要追赶机制，因为回放日志就是状态。"""
    if 事件们 is None:#无日志
        return None#从未切换
    for 下标 in range(len(事件们)-1,-1,-1):#从后往前
        事件=事件们[下标]#当前事件
        if 取字段(事件,'type')=='sandbox/mode':#最近一次切换
            return 取字段(取字段(事件,'data'),'mode')#返回模式
    return None#从未切换

def 设沙盒模式(会话,模式):#写入会话覆盖
    """会话沙箱模式覆盖的唯一写入路径：恰好追加一条 `sandbox/mode` 事件——切换就是它的事件；没有任何东西在带外改模式状态。在该会话下一次隔离调用（bash 或 fs）时生效——消费方每次读取都折叠。"""
    追加=getattr(会话,'追加',None)#中文追加
    if callable(追加):#有中文追加
        追加('sandbox/mode',{'mode':模式})#追加一条切换事件
        return#写完
    会话.append('sandbox/mode',{'mode':模式})#英文追加回落
