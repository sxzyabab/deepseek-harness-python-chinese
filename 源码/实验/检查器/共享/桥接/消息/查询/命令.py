"""封闭的非 CDP Inspector 查询与结果模型。

对齐上游 `shared/bridge/messages/query/commands.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    'cordis树获取查询','检查器查询','cordis树获取结果','检查器查询结果',
    '检查器查询错误','检查器查询请求器',
]#公开面结束

def cordis树获取查询():#取树查询
    """读取最新已提交的 Cordis 运行时树。"""
    return {'op':'cordis-tree/get'}#取树查询

检查器查询=dict#查询联合

def cordis树获取结果(tree):#取树结果
    """读取最新已提交 Cordis 运行时树的结果。"""
    return {'op':'cordis-tree/get','tree':tree}#取树结果

检查器查询结果=dict#结果联合

查询错误码=('invalid-request','stale-source','result-too-large','internal-error')#错误码

def 检查器查询错误(code,message):#查询错误
    """稳定的 Worker 侧查询失败。"""
    return {'code':code,'message':message}#错误

class 检查器查询请求器:#查询请求器
    """由共享相关查询所有者实现的 Host/Client 接口。"""
    def 请求(自身,查询):#执行查询
        """对当前已连接的源世代执行一次查询。"""
        raise NotImplementedError#子类实现
