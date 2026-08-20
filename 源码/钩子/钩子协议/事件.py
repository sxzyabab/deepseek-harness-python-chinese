"""持久、仅日志的钩子事件的追加助手。它们不带界面意图，必须包在一轮之内且调用/结果成对。轮中钩子点满足该边界；SessionStart 改为记录注入的上下文，不会在轮外追加 hook/*。"""

默认stderr摘要最大字符=500#stderr 摘要默认上限
钩子调用=dict#一次钩子调用的身份字段
钩子结果记录=dict#一次钩子结果记录字段

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 摘要stderr(标准错误,最大字符):#截断 stderr 作摘要
    """为 stderrSummary 截断钩子 stderr：先去空白，空则 None，超过上限则切开并加省略号。"""
    修剪=(标准错误 or '').strip()#去掉首尾空白
    if len(修剪)==0:#空白则无摘要
        return None#缺席
    if len(修剪)>最大字符:#超上限则切开并加省略号
        return 修剪[0:最大字符]+'…'#封顶
    return 修剪#原文

def 追加钩子调用(会话,调用):#追加 hook/invoked
    """向会话追加一条 hook/invoked 事件，写明处理器和钩子点。缺省的 matcher 不写入载荷。"""
    载荷={#调用事件载荷
        'turn':取字段(调用,'turn'),#所在轮次
        'point':取字段(调用,'point'),#钩子点名
        'dialect':取字段(调用,'dialect'),#桥接方言
        'handlerId':取字段(调用,'handlerId'),#处理器 id
    }#基础字段
    匹配器=取字段(调用,'matcher')#匹配模式
    if 匹配器 is not None:#有匹配模式才写入
        载荷['matcher']=匹配器#写入
    追加=getattr(会话,'追加',None) or getattr(会话,'append',None)#追加入口
    追加('hook/invoked',载荷)#写入调用事件

def 追加钩子结果(会话,记录):#追加 hook/result
    """追加与 hook/invoked 成对的持久结果。记下的决策依次是已解析决策，再是 continue:false 时的 stop，否则 pass。"""
    输出=取字段(记录,'output')#取出解码结果
    摘要=摘要stderr(取字段(输出,'stderr') or '',取字段(记录,'stderrSummaryMaxChars'))#生成 stderr 摘要
    判定=取字段(输出,'decision')#已解析决策
    if 判定 is None:#无显式决策
        if 取字段(输出,'continue') is False:#continue 假为 stop
            判定='stop'#停止
        else:#否则 pass
            判定='pass'#放行
    载荷={#结果事件载荷
        'turn':取字段(记录,'turn'),#所在轮次
        'point':取字段(记录,'point'),#钩子点名
        'handlerId':取字段(记录,'handlerId'),#处理器 id
        'decision':判定,#记下的判定
        'durationMs':取字段(记录,'durationMs'),#运行毫秒数
    }#基础字段
    退出码=取字段(输出,'exitCode')#进程退出码
    if 退出码 is not None:#有退出码才写入
        载荷['exitCode']=退出码#写入
    if 摘要 is not None:#有摘要才写入
        载荷['stderrSummary']=摘要#写入
    追加=getattr(会话,'追加',None) or getattr(会话,'append',None)#追加入口
    追加('hook/result',载荷)#写入结果事件
