"""与 Client 界域只读源目录交换的操作与值。

对齐上游 `shared/bridge/messages/sources/commands.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '客户端脚本描述','客户端源内容种类','客户端源命令','客户端源结果','客户端源错误',
]#公开面结束

客户端脚本描述=dict#Client脚本描述
客户端源内容种类=('source','source-map')#内容种类

def 客户端源命令(op,**字段):#源命令联合
    """Client 源目录接受的只读操作。"""
    return {'op':op,**字段}#命令

def 客户端源结果(op,**字段):#源结果联合
    """一次 Client 源操作的成功结果。"""
    return {'op':op,**字段}#结果

客户端源错误码=('invalid-request','script-not-found','load-failed','result-too-large','internal-error')#错误码

def 客户端源错误(code,message):#源错误
    """Client 源目录故意返回的失败。"""
    return {'code':code,'message':message}#错误
