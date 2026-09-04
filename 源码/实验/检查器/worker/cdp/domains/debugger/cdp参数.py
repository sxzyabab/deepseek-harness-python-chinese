"""共享域处理的 CDP Debugger 请求校验。"""
#对齐上游 worker/cdp/domains/debugger/cdp-params.ts

__all__=['解析调用帧求值','取请求脚本id']#仅中文公开名

def _精确键(参数,允许键,标签):#精确键校验
    """拒绝未声明键。"""
    for 键 in 参数:#扫键
        if 键 not in 允许键:#多余
            raise ValueError(f'{标签} has unexpected key {键}')#抛错

def _可选布尔(参数,键):#可选布尔
    """有则校验为布尔。"""
    if 键 not in 参数:#缺省
        return {}#空
    值=参数[键]#取值
    if not isinstance(值,bool):#类型
        raise ValueError(f'{键} must be a boolean')#抛错
    return {键:值}#字段

def _可选字符串(参数,键):#可选字符串
    """有则校验为字符串。"""
    if 键 not in 参数:#缺省
        return {}#空
    值=参数[键]#取值
    if not isinstance(值,str):#类型
        raise ValueError(f'{键} must be a string')#抛错
    return {键:值}#字段

def 解析调用帧求值(参数):#解析调用帧求值
    """解析 Debugger.evaluateOnCallFrame，不静默接受不支持的选项。"""
    _精确键(参数,[#精确键
        'callFrameId','expression','objectGroup','includeCommandLineAPI','silent','returnByValue',#常用
        'generatePreview','throwOnSideEffect','timeout',#其余
    ],'Debugger.evaluateOnCallFrame parameters')#标签
    if not isinstance(参数.get('callFrameId'),str) or not isinstance(参数.get('expression'),str):#缺必填
        raise ValueError('Debugger.evaluateOnCallFrame requires callFrameId and expression')#抛错
    超时=参数.get('timeout')#timeout
    if 超时 is not None and (not isinstance(超时,(int,float)) or isinstance(超时,bool) or 超时<0):#非法
        raise ValueError('Debugger.evaluateOnCallFrame timeout must be a non-negative number')#抛错
    结果={#请求
        'callFrameId':参数['callFrameId'],#调用帧
        'expression':参数['expression'],#表达式
        **_可选字符串(参数,'objectGroup'),#对象组
        **_可选布尔(参数,'includeCommandLineAPI'),#命令行API
        **_可选布尔(参数,'silent'),#静默
        **_可选布尔(参数,'returnByValue'),#按值返回
        **_可选布尔(参数,'generatePreview'),#预览
        **_可选布尔(参数,'throwOnSideEffect'),#副作用抛错
    }#结果结束
    if 超时 is not None:#有超时
        结果['timeoutMs']=超时#超时毫秒
    return 结果#返回

def 取请求脚本id(参数):#取脚本id
    """查找直接携带或由 Debugger 位置参数携带的 ScriptId。"""
    if isinstance(参数.get('scriptId'),str):#直接字段
        return 参数['scriptId']#返回
    for 键 in ('location','start','end'):#位置字段
        值=参数.get(键)#取值
        if not isinstance(值,dict):#非对象
            continue#下一个
        脚本id=值.get('scriptId')#嵌套scriptId
        if isinstance(脚本id,str):#命中
            return 脚本id#返回
    return None#未找到
