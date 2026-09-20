"""按会话的沙箱模式覆盖：会话日志即存储。

运行时切换（UI 政策控件或测试场景）作为 `sandbox/mode` 事件记在适用会话上；`effective = fold(events) ?? 部署默认`，覆盖经回放挺过重启，会话互不可见，无外部配置存储。该事件只进日志（`approval/*` 先例）：政策所有者把折叠投影进每次模型请求；强制工具报告操作级边界标记。执行经沙盒政策解析遵守同一折叠——模式与工作区根盖到每次能力调用，优先级弱于升级授予。

覆盖是 bash 与文件系统共享的政策状态，放在政策包而非任一能力侧。

会话事件映射扩展（文档约定）：
`sandbox/mode`：会话沙箱模式被切换——只进日志（非展示事件，不带 `surfaceOp`）；持久可回放，从不进模型文本。最后一条为此会话覆盖。`source: 'delegation'` 标记播种进子智能体的覆盖；缺失 source 为运行时切换。载荷：`mode`（SandboxMode）、可选 `source`（`'delegation'`）。
"""
沙盒模式表=('read-only','workspace-write','danger-full-access')#每一个 SandboxMode，供选项广告与对不受信任模式字符串的运行时校验

def 生效沙盒模式(事件列表):
    """会话的沙箱模式覆盖：日志里最后一条 `sandbox/mode` 事件；会话从未切换过则为 None（调用方应用部署默认）。纯折叠——恢复不需要追赶机制，因为回放日志就是状态。事件是 dict。"""
    if 事件列表 is None:#无日志
        return None#从未切换
    for 下标 in range(len(事件列表)-1,-1,-1):#从后往前
        事件=事件列表[下标]#当前事件
        if 事件['type']=='sandbox/mode':#最近一次切换
            return 事件['data']['mode']#返回模式
    return None#从未切换

def 设沙盒模式(会话,模式):
    """会话沙箱模式覆盖的唯一写入路径：恰好追加一条 `sandbox/mode` 事件。会话是对象。"""
    会话.追加('sandbox/mode',{'mode':模式})#追加一条切换事件
