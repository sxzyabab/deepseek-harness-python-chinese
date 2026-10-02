'按会话的沙箱模式覆盖：会话日志即存储'
沙盒模式表=('read-only','workspace-write','danger-full-access')#每一个 SandboxMode，供选项广告与对不受信任模式字符串的运行时校验

def 生效沙盒模式(事件列表):
    """会话的沙箱模式覆盖：日志里最后一条 `sandbox/mode` 事件；会话从未切换过则为 None（调用方应用部署默认）。
    纯折叠——恢复不需要追赶机制，因为回放日志就是状态。
    事件是 dict
    """
    if 事件列表 is None:#无日志
        return None#从未切换
    for 下标 in range(len(事件列表)-1,-1,-1):#从后往前
        事件=事件列表[下标]#当前事件
        if 事件['type']=='sandbox/mode':#最近一次切换
            return 事件['data']['mode']#返回模式
    return None#从未切换

def 设沙盒模式(会话,模式):
    """会话沙箱模式覆盖的唯一写入路径：恰好追加一条 `sandbox/mode` 事件。
    会话是对象
    """
    会话.追加('sandbox/mode',{'mode':模式})#追加一条切换事件
