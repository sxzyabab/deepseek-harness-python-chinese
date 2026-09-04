"""测试拥有的工作区面：可观察源外加已记录动作。

对齐上游 `client-runtime/src/workspaces.ts`。公开面仅中文名。
"""
from .夹具 import 工作区快照#工作区快照工厂

__all__=['测试工作区']#仅中文公开名

def 创建快照存储(初值):#简易快照存储
    """对齐 createSnapshotStore：getSnapshot/subscribe/update。"""
    状态=[dict(初值)]#状态盒
    监听者=set()#订阅者
    def 取快照():#读快照
        """返回当前状态。"""
        return 状态[0]#状态
    def 订阅(回调):#订阅
        """登记变更。"""
        监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            监听者.discard(回调)#删除
        return 退订#退订器
    def 更新(变换):#就地变换
        """调用变换(state) 并通知。"""
        变换(状态[0])#变换
        for 回调 in list(监听者):#通知
            回调()#触发
    return {'getSnapshot':取快照,'subscribe':订阅,'update':更新}#存储面

class 测试工作区:#工作区测试替身
    """实现 IWorkspaces 面；动作记入 calls。"""

    def __init__(自身,稳定):#构造
        """记下稳定器并播种空列表。"""
        自身._stabilize=稳定#稳定器
        自身.list=创建快照存储(工作区快照())#列表源
        自身.calls=[]#调用记录
        自身._stubs={}#桩表

    def update(自身,变换):#更新列表
        """经草稿更新工作区列表状态。"""
        自身._stabilize(lambda:自身.list['update'](变换))#稳定内更新

    def stub(自身,方法,实现):#安装桩
        """替换一个动作的行为。"""
        自身._stubs[方法]=实现#安装桩

    def create(自身,输入):#创建工作区
        """创建 Workspace（已记录）。"""
        自身.calls.append({'method':'create','args':[输入]})#记录
        桩=自身._stubs.get('create')#取桩
        if 桩 is not None:#有桩
            return 桩(输入)#走桩
        return {'workspaceId':f"ws-{输入['path']}",'title':输入['path'],'path':输入['path'],'sessionIds':[]}#默认回声

    def rename(自身,工作区标识,标题):#重命名
        """重命名 Workspace（已记录）。"""
        自身.calls.append({'method':'rename','args':[工作区标识,标题]})#记录
        桩=自身._stubs.get('rename')#取桩
        if 桩 is not None:#有桩
            return 桩(工作区标识,标题)#走桩
        return {'workspaceId':工作区标识,'title':标题,'path':f'/{标题}','sessionIds':[]}#默认回声

    def delete(自身,工作区标识):#删除
        """删除 Workspace（已记录）。"""
        自身.calls.append({'method':'delete','args':[工作区标识]})#记录
        桩=自身._stubs.get('delete')#取桩
        if 桩 is not None:#有桩
            return 桩(工作区标识)#走桩
        return None#无操作

    def insertBefore(自身,工作区标识,锚点=None):#移动工作区
        """在显示顺序中移动 Workspace。"""
        自身.calls.append({'method':'insertBefore','args':[工作区标识,锚点]})#记录
        桩=自身._stubs.get('insertBefore')#取桩
        if 桩 is not None:#有桩
            return 桩(工作区标识,锚点)#走桩
        return None#无操作

    def insertSessionBefore(自身,工作区标识,会话标识,锚点=None):#移动会话
        """移动一个已记账会话。"""
        自身.calls.append({'method':'insertSessionBefore','args':[工作区标识,会话标识,锚点]})#记录
        桩=自身._stubs.get('insertSessionBefore')#取桩
        if 桩 is not None:#有桩
            return 桩(工作区标识,会话标识,锚点)#走桩
        return {'workspaceId':工作区标识,'title':'','path':'','sessionIds':[会话标识]}#默认回声

    def archiveSession(自身,会话标识):#归档会话
        """归档会话（已记录）。"""
        自身.calls.append({'method':'archiveSession','args':[会话标识]})#记录
        桩=自身._stubs.get('archiveSession')#取桩
        if 桩 is not None:#有桩
            return 桩(会话标识)#走桩
        def 写入(草稿):#默认更新
            """加入归档集。"""
            草稿['archivedSessionIds']=[*草稿['archivedSessionIds'],会话标识]#加入
        自身.update(写入)#默认更新
        return None#完成

TestWorkspaces=测试工作区#上游名
