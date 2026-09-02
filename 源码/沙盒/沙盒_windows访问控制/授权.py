"""服务端写入授权物化。沙箱 seam 为每个工作区持有一份常驻工作区授权，并为每个在场会话/工作区对持有一份可撤销临时授权。工作区身份靠确定性推导及其常驻 ACE 存活；临时身份从随机私有路径推导，重启后故意是新的。

失败即关闭：`add` 在任何授权失败时抛出，调用方拆除实例（撤销迄今已授权的每条路径）；`dispose` 撤销每份可撤销授权并报告每次清理失败。
"""
from ...依赖 import cordis#外部依赖胶水
from .acl import 授予写入,撤销写入#授予与撤销写入ACE
from .ffi import 分配指针槽,解码指针,是否空指针,抛上次错误,同步解析绑定#指针槽、解码、空指针、错误抛出与同步绑定

聚合错误=cordis.聚合错误#汇总多次清理失败

class ACL写入授权:#一份写入SID的授权物化
    """一个写入 SID 在提供方生命周期内的授权物化：已解析 SID 指针，外加当前 DACL 携带其 ACE 的每个目录。工作区路径以常驻方式加入（其 ACE 是跨会话复用缓存，比本授权活得更久——dispose() 跳过撤销它们）；临时路径可撤销（dispose() 撤销它们）。用 create / 创建 创建；dispose 撤销可撤销路径并释放 SID。"""
    def __init__(自身,接口,sid指针,写入SID):#保存绑定、指针与SID
        """保存绑定、指针与 SID。"""
        自身.api=接口#记下绑定
        自身._sidPtr=sid指针#记下SID指针
        自身.writeSid=写入SID#记下SID字符串
        自身._revocablePaths=[]#可撤销路径
        自身._standingPaths=[]#常驻路径

    @staticmethod#工厂
    def 创建(写入SID,接口=None):#解析SID并打开绑定
        """解析 SID 字符串并打开绑定表。失败即关闭。"""
        绑定=接口 if 接口 is not None else 同步解析绑定()#给定绑定或惰性加载
        sid槽=分配指针槽()#接收SID指针的槽
        if 绑定.convertStringSidToSidW(写入SID,sid槽)==0:#转换失败
            抛上次错误(绑定,'ConvertStringSidToSidW',写入SID)#带SID字符串抛出
        sid指针=解码指针(sid槽)#取出指针
        if sid指针 is None:#空指针
            抛上次错误(绑定,'ConvertStringSidToSidW','null SID for '+写入SID)#空指针则失败
        return ACL写入授权(绑定,sid指针,写入SID)#尚无ACE的就绪授权

    def 添加(自身,路径,常驻=False):#授予一条路径
        """在一个目录上授予写入 ACE，并记下路径供拆除使用。"""
        (自身._standingPaths if 常驻 else 自身._revocablePaths).append(路径)#先记下，失败后仍能撤销
        授予写入(自身.api,路径,自身._sidPtr)#写入ACE

    @property#只读
    def paths(自身):#已授权路径
        """当前携带该授权的每个目录，按授予顺序。"""
        return [*自身._standingPaths,*自身._revocablePaths]#常驻在前，可撤销在后

    def 拆除(自身):#拆除授权
        """撤销每份可撤销授权并释放 SID；报告每次清理失败。"""
        失败们=[]#清理失败
        for 路径 in 自身._revocablePaths:#逐条可撤销路径
            try:#撤销可能失败
                撤销写入(自身.api,路径,自身._sidPtr)#去掉ACE
            except BaseException as 错误:#撤销失败
                失败们.append(错误)#记下，继续其余
        try:#释放SID
            释放=自身.api.localFree(自身._sidPtr)#LocalFree
            if not 是否空指针(释放):#非空返回表示失败
                抛上次错误(自身.api,'LocalFree','write SID')#抛出
        except BaseException as 错误:#释放失败
            失败们.append(错误)#记下
        if len(失败们)>0:#有清理失败
            raise 聚合错误(失败们,'AclWriteGrant dispose completed with '+str(len(失败们))+' cleanup failure(s)')#汇总抛出
