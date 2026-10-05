'JSON-RPC 2.0 的消息构造、消息分类与请求响应配对（不绑定传输，可与 帧协议 组合）'
from threading import Lock as 锁类#互斥锁
from .并发原语 import 操作任务#等待响应的一次性任务

__all__=[
    '解析错误码','无效请求码','方法未找到码','无效参数码','内部错误码','jsonrpc响应错误',
    '构造jsonrpc请求','构造jsonrpc通知','构造jsonrpc成功响应','构造jsonrpc错误响应',
    '分类jsonrpc消息','未决请求表',
]#仅中文公开名

解析错误码=-32700#收到的不是合法JSON
无效请求码=-32600#不是合法的请求对象
方法未找到码=-32601#方法不存在
无效参数码=-32602#参数不合法
内部错误码=-32603#处理时内部出错

class jsonrpc响应错误(Exception):
    '对端以 error 对象响应；码、消息、数据取自 error 对象'
    def __init__(自身,码,消息:str,数据=None):
        '码不是整数时为 None'
        super().__init__(消息)
        自身.码=码
        自身.消息=消息
        自身.数据=数据

def 构造jsonrpc请求(标识,方法:str,参数=None)->dict:
    '请求对象；参数为 None 时不写 params 成员'
    消息={'jsonrpc':'2.0','id':标识,'method':方法}
    if 参数 is not None:
        消息['params']=参数
    return 消息

def 构造jsonrpc通知(方法:str,参数=None)->dict:
    '通知对象（没有 id，对端不会响应）；参数为 None 时不写 params 成员'
    消息={'jsonrpc':'2.0','method':方法}
    if 参数 is not None:
        消息['params']=参数
    return 消息

def 构造jsonrpc成功响应(标识,结果)->dict:
    '成功响应对象'
    return {'jsonrpc':'2.0','id':标识,'result':结果}

def 构造jsonrpc错误响应(标识,码:int,消息:str,数据=None)->dict:
    '错误响应对象；数据为 None 时不写 data 成员'
    错误体={'code':码,'message':消息}
    if 数据 is not None:
        错误体['data']=数据
    return {'jsonrpc':'2.0','id':标识,'error':错误体}

def 分类jsonrpc消息(消息)->str:
    '按成员判定消息种类，返回 "请求"、"通知"、"响应" 或 "无效"。id 只认字符串与非布尔数字'
    if not isinstance(消息,dict):
        return '无效'
    标识=消息.get('id')
    有标识=isinstance(标识,str) or (isinstance(标识,(int,float)) and not isinstance(标识,bool))
    if isinstance(消息.get('method'),str):
        return '请求' if 有标识 else '通知'
    if 有标识 and ('result' in 消息 or 'error' in 消息):
        return '响应'
    return '无效'

class 未决请求表:
    '线程安全地管理已发出、等待响应的请求：分配 id，收到响应后兑现或拒绝对应任务'
    def __init__(自身):
        '创建空表，id 从 1 起递增'
        自身._锁=锁类()
        自身._任务表={}
        自身._下一标识=1

    def 新建请求(自身)->tuple:
        '分配 id 并登记等待任务，返回 (id, 操作任务)；调用方发出请求后对任务调用 等待'
        with 自身._锁:
            标识=自身._下一标识
            自身._下一标识+=1
            任务=操作任务()
            自身._任务表[标识]=任务
        return 标识,任务

    def 撤销(自身,标识):
        '请求没能发出时撤销登记；不存在则无效果'
        with 自身._锁:
            自身._任务表.pop(标识,None)

    def 处理响应(自身,响应:dict)->bool:
        '按 id 认领一条已分类为响应的消息：有 error 对象则拒绝为 jsonrpc响应错误，否则以 result 兑现。id 未登记返回 False'
        with 自身._锁:
            任务=自身._任务表.pop(响应['id'],None)
        if 任务 is None:
            return False
        错误体=响应.get('error')
        if isinstance(错误体,dict):
            码=错误体.get('code')
            文案=错误体.get('message')
            任务.拒绝(jsonrpc响应错误(
                码 if isinstance(码,int) and not isinstance(码,bool) else None,
                文案 if isinstance(文案,str) else 'JSON-RPC 错误',
                错误体.get('data'),
            ))
        else:
            任务.兑现(响应.get('result'))
        return True

    def 全部拒绝(自身,错误):
        '以同一个错误拒绝所有未决请求并清空，连接断开或关闭时调用'
        with 自身._锁:
            任务列表=list(自身._任务表.values())
            自身._任务表.clear()
        for 任务 in 任务列表:
            任务.拒绝(错误)
