"""Client 线上值到 realm 中立 Runtime 值的转换。"""
#对齐上游 worker/realms/client/values.ts

__all__=[#仅中文公开名
    'Client完成','Client属性','Client内部属性','Client异常',
    'Client控制台事件','Client远程对象','Client句柄',
]#公开面结束

def Client句柄(值):#Client句柄
    """将公共后端句柄重标记为拥有它的 Client 传输角色。"""
    return 值#包装

def _后端句柄(值):#后端句柄
    """后端中立句柄。"""
    return 值#包装

def Client远程对象(值):#Client远程对象
    """将 Client RemoteObject 转换到后端中立句柄槽。"""
    结果={'descriptor':值['descriptor']}#结果
    if 'object' in 值 and 值['object'] is not None:#对象
        结果['object']={'handle':_后端句柄(值['object']['handle'])}#句柄
    if 'semanticReference' in 值:#语义引用
        结果['semanticReference']=值['semanticReference']#写入
    return 结果#返回

def Client栈(值,映射脚本键):#Client栈
    """递归转换栈跟踪。"""
    结果={}#栈
    if 'description' in 值:#描述
        结果['description']=值['description']#写入
    结果['callFrames']=[{#帧
        **帧,#展开
        **({'scriptKey':映射脚本键(帧['scriptKey'])} if 'scriptKey' in 帧 else {}),#脚本键
    } for 帧 in 值['callFrames']]#map
    if 'parent' in 值:#父栈
        结果['parent']=Client栈(值['parent'],映射脚本键)#递归
    return 结果#返回

def Client异常(值,映射脚本键):#Client异常
    """转换 Client 异常详情及其可选对象。"""
    异常=值.get('exception')#异常对象
    详情={键:项 for 键,项 in 值.items() if 键 not in ('exception',)}#其余
    if 'stackTrace' in 值:#栈
        详情['stackTrace']=Client栈(值['stackTrace'],映射脚本键)#转换
    if 异常 is not None:#有异常
        详情['exception']=Client远程对象(异常)#转换
    return 详情#返回

def Client完成(结果,映射脚本键):#Client完成
    """转换一次 Client 完成及其全部嵌套对象。"""
    完成=结果['completion']#完成体
    输出={'result':Client远程对象(完成['result'])}#结果对象
    if 'exceptionDetails' in 完成:#异常
        输出['exceptionDetails']=Client异常(完成['exceptionDetails'],映射脚本键)#含异常
    return 输出#返回

def Client属性(值):#Client属性
    """转换一个 Client 属性描述符及其全部嵌套对象。"""
    结果={键:项 for 键,项 in 值.items() if 键 not in ('value','get','set','symbol')}#其余
    if 'value' in 值:#值
        结果['value']=Client远程对象(值['value'])#转换
    if 'get' in 值:#getter
        结果['get']=Client远程对象(值['get'])#转换
    if 'set' in 值:#setter
        结果['set']=Client远程对象(值['set'])#转换
    if 'symbol' in 值:#符号
        结果['symbol']=Client远程对象(值['symbol'])#转换
    return 结果#返回

def Client内部属性(值):#Client内部属性
    """转换一个 Client 内部属性描述符。"""
    结果={'name':值['name']}#名
    if 'value' in 值:#值
        结果['value']=Client远程对象(值['value'])#转换
    return 结果#返回

def Client控制台事件(值,映射脚本键):#Client Console事件
    """递归转换一个 Client Console 事件。"""
    if 值['type']=='console-api':#API事件
        事件={**值['event'],'arguments':[Client远程对象(项) for 项 in 值['event']['arguments']]}#载荷
        if 'stackTrace' in 值['event']:#栈
            事件['stackTrace']=Client栈(值['event']['stackTrace'],映射脚本键)#含栈
        return {'type':值['type'],'event':事件}#结果
    return {#异常事件
        'type':值['type'],#类型
        'event':{**值['event'],'details':Client异常(值['event']['details'],映射脚本键)},#详情
    }#return结束
