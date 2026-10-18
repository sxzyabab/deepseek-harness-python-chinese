'浏览器侧再导出的连接协议辅助'
from ..rpc import Rpc标识,传输错误#关联与传输失败

RpcId=Rpc标识#与上游导出名相同
transportError=传输错误#与上游导出名相同


def 结果槽(响应):
    '取出一元响应里的业务结果'
    if isinstance(响应,dict):#字典
        return 响应['result']#结果
    return 响应.result#对象上的结果
