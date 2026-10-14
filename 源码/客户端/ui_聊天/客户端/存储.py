from ....基础设施.通用工具 import 观察者集合
from .约定.存储 import 初始聊天状态,回合过程视图条目#存储契约

__all__=['已存回合过程条目','创建聊天存储','聊天存储']#仅中文公开名

def 已存回合过程条目(状态,回合):
    '解析某一 Turn 上手动展开的正文记录。状态为 dict'
    表=状态['turnProcesses'] if 'turnProcesses' in 状态 and 状态['turnProcesses'] is not None else []#表
    for 条目 in 表:#逐条
        if 'turn' in 条目 and 条目['turn']==回合:#命中轮次
            return 条目#返回
    return None#缺失

class 聊天存储:
    '选中与过程展开。槽位解析器按 getSnapshot、subscribe、actions、create 读取'
    def __init__(自身):
        '空选中、空展开'
        自身.状态={'selection':初始聊天状态['selection'],'turnProcesses':[]}#独立列表
        自身.监听者=观察者集合()#订阅
        自身.actions={'select':自身.选中,'setTurnProcessOpen':自身.设回合过程展开}#动作

    def getSnapshot(自身):
        '当前状态引用'
        return 自身.状态#快照

    def subscribe(自身,回调):
        '登记变更回调，返回退订'
        return 自身.监听者.订阅(回调)#退订

    def create(自身,键=None):
        '根作用域交回这一份；每个会话键另造一份'
        if 键 is None:#根
            return 自身#共享
        return 聊天存储()#会话一份

    def 选中(自身,目标):
        '写入 selection'
        自身.状态['selection']=目标#写
        自身.监听者.通知()#广播

    def 设回合过程展开(自身,回合,正文步,展开):
        '展开写入；收起移除'
        表=自身.状态['turnProcesses']#列表
        索引=-1#定位
        for 序,条目 in enumerate(表):#扫
            if 'turn' in 条目 and 条目['turn']==回合:#同轮
                索引=序
                break
        if 展开 is not True:#收起
            if 索引>=0:
                表.pop(索引)#删
                自身.监听者.通知()#广播
            return
        下一=回合过程视图条目(回合,正文步)#展开记录
        if 索引<0:#新增
            表.append(下一)#推
        else:#覆盖
            表[索引]=下一#写
        自身.监听者.通知()#广播

def 创建聊天存储():
    '每个已渲染 Session 作用域由 create 再实例化一次。只暴露 actions，不另开顶层别名'
    return 聊天存储()#句柄
