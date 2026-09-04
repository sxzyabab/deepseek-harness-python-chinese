"""按 Session 的 Chat 选中 store，供 transcript 与详情面板共享。

对齐上游 `ui-chat/src/client/stores.ts`。公开面仅中文名。
"""
from .约定.仓库 import 初始聊天状态,回合过程视图条目#store 契约

__all__=['已存回合过程条目','创建聊天仓库']#仅中文公开名

def 已存回合过程条目(状态,回合):#取已存过程展开条目
    """解析某一 Turn 上手动展开的正文记录。"""
    for 条目 in 状态.get('turnProcesses') or []:#逐条
        if 条目.get('turn')==回合:#命中轮次
            return 条目#返回
    return None#缺失

def 创建聊天仓库():#创建选中 store 句柄
    """每个已渲染 Session 作用域实例化一次。"""
    状态=dict(初始聊天状态)#可变状态
    状态['turnProcesses']=[]#独立列表
    def 选中(目标):#改选中目标
        """写入 selection。"""
        状态['selection']=目标#写
    def 设回合过程展开(回合,正文步,展开):#改某轮过程展开态
        """展开写入；收起移除。"""
        表=状态['turnProcesses']#列表
        索引=-1#定位
        for 序,条目 in enumerate(表):#扫
            if 条目.get('turn')==回合:#同轮
                索引=序#记下
                break#停
        if not 展开:#收起
            if 索引>=0:#有
                表.pop(索引)#删
            return#完成
        下一=回合过程视图条目(回合,正文步)#展开记录
        if 索引<0:#新增
            表.append(下一)#推
        else:#覆盖
            表[索引]=下一#写
    return {#句柄
        'getSnapshot':lambda:状态,#快照
        'actions':{'select':选中,'setTurnProcessOpen':设回合过程展开},#动作
        'select':选中,#便捷
        'setTurnProcessOpen':设回合过程展开,#便捷
    }#结束
