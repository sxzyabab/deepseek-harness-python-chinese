"""由 Client 执行的 Runtime 操作的封闭命令/结果协议。

对齐上游 `shared/bridge/messages/runtime/commands.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '客户端运行时远程对象','客户端运行时属性描述符','客户端运行时内部属性描述符',
    '客户端运行时异常详情','客户端调用参数','客户端运行时命令','客户端运行时完成',
    '客户端运行时结果','客户端运行时错误',
]#公开面结束

客户端运行时远程对象=dict#Client远程对象
客户端运行时属性描述符=dict#Client属性描述符
客户端运行时内部属性描述符=dict#Client内部属性
客户端运行时异常详情=dict#Client异常详情
客户端调用参数=dict#Client调用参数

def 客户端运行时命令(op,**字段):#Runtime命令联合
    """Client Runtime 传输实现的封闭命令集。"""
    return {'op':op,**字段}#命令

客户端运行时完成=dict#Client完成结果

def 客户端运行时结果(op,**字段):#Runtime结果联合
    """结果判别镜像命令，并防止跨方法结算。"""
    return {'op':op,**字段}#结果

客户端运行时错误码=('invalid-request','object-not-found','unsupported','timeout','result-too-large','internal-error')#错误码

def 客户端运行时错误(code,message):#Runtime传输错误
    """与已求值 JavaScript 异常相区分的、稳定的传输级失败。"""
    return {'code':code,'message':message}#错误
