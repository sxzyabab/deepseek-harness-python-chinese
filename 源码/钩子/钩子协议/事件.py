默认stderr摘要最大字节=500#stderr 摘要默认上限（按 UTF-8 字节计；线协议键仍为 stderrSummaryMaxChars）
钩子调用=dict#一次钩子调用的身份字段
钩子结果记录=dict#一次钩子结果记录字段

def 按utf8字节截断(文本,最大字节):
    """按 UTF-8 字节截断，切点落在字符边界。"""
    数据=文本.encode('utf-8')#编码
    if len(数据)<=最大字节:#未超
        return 文本#原文
    切=最大字节#拟切点
    while 切>0 and (数据[切]&0xC0)==0x80:#续字节则回退到字符起始
        切-=1#回退
    return 数据[0:切].decode('utf-8')#解码到边界

def 摘要stderr(标准错误,最大字节):
    """为 stderrSummary 按 UTF-8 字节截断钩子 stderr：先去空白，空则 None，超过上限则切开并加省略号。"""
    修剪=(标准错误 if 标准错误 is not None else '').strip()#去掉首尾空白
    if len(修剪)==0:#空白则无摘要
        return None#省略键
    编码=修剪.encode('utf-8')#按字节量预算
    if len(编码)>最大字节:#超上限则切开并加省略号
        return 按utf8字节截断(修剪,最大字节)+'…'#封顶
    return 修剪#原文

def 追加钩子调用(会话,调用):
    """向会话追加一条 hook/invoked 事件，写明处理器和钩子点。缺省的 matcher 不写入载荷。调用是 dict，会话是对象。"""
    载荷={#调用事件载荷
        'turn':调用['turn'],#所在轮次
        'point':调用['point'],#钩子点名
        'dialect':调用['dialect'],#桥接方言
        'handlerId':调用['handlerId'],#处理器 id
    }#基础字段
    if 'matcher' in 调用:#有匹配模式才写入
        载荷['matcher']=调用['matcher']#写入
    会话.追加('hook/invoked',载荷)#写入调用事件

def 追加钩子结果(会话,记录):
    """追加与 hook/invoked 成对的持久结果。记下的决策依次是已解析决策，再是 continue:false 时的 stop，否则 pass。记录与输出都是 dict。"""
    输出=记录['output']#取出解码结果
    标准错误=输出['stderr'] if 'stderr' in 输出 else ''#stderr 文本
    摘要=摘要stderr(标准错误,记录['stderrSummaryMaxChars'])#生成 stderr 摘要
    if 'decision' in 输出:#有显式决策
        判定=输出['decision']#已解析决策
    elif 'continue' in 输出 and 输出['continue'] is False:#continue 假为 stop
        判定='stop'#停止
    else:
        判定='pass'#放行
    载荷={#结果事件载荷
        'turn':记录['turn'],#所在轮次
        'point':记录['point'],#钩子点名
        'handlerId':记录['handlerId'],#处理器 id
        'decision':判定,#记下的判定
        'durationMs':记录['durationMs'],#运行毫秒数
    }#基础字段
    if 'exitCode' in 输出 and 输出['exitCode'] is not None:#有退出码才写入；0 是合法退出码
        载荷['exitCode']=输出['exitCode']#写入
    if 摘要 is not None:#有摘要才写入
        载荷['stderrSummary']=摘要#写入
    会话.追加('hook/result',载荷)#写入结果事件
