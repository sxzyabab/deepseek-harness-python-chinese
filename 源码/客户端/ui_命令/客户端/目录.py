import threading
from ..异常 import 目录等待中止原因
from .解析 import 第一方定义,拼写别名

__all__=['命令目录']

def 信号已中止(信号):
    'AbortSignal 认 aborted，触发源传来的 Event 认 is_set'
    if hasattr(信号,'aborted'):
        return bool(信号.aborted)
    return 信号.is_set()

class 目录格子:
    '一场会话的目录缓存格'
    def __init__(自身):
        '从未拉过'
        自身.状态='cold'
        自身.命令表=()
        自身.代次=0
        自身.最近错误=None
        自身.等待者=[]

class 命令目录:
    '按会话缓存宿主命令目录。事件和远程调用由拥有它的服务来接'
    def __init__(自身,拉命令):
        '记下按会话拉目录的回调'
        自身.拉命令=拉命令
        自身.格子表={}

    def 取状态(自身,会话标识):
        '这场会话现在的缓存状态。没碰过是 cold'
        if 会话标识 not in 自身.格子表:
            return 'cold'
        return 自身.格子表[会话标识].状态

    def 解析(自身,会话标识,名):
        '在就绪目录上同步查找。精确名优先，再按中英文令牌别名'
        if 会话标识 not in 自身.格子表:
            return None
        格子=自身.格子表[会话标识]
        if 格子.状态!='ready':
            return None
        for 描述符 in 格子.命令表:
            if 描述符['name']==名:
                return 描述符
        if 名 not in 拼写别名:
            return None
        方名=拼写别名[名]
        包名=第一方定义[方名]
        for 描述符 in 格子.命令表:
            if 描述符.get('definitionId')==包名:
                return 描述符
        return None

    def 全部失效(自身):
        '软失效：每个已经碰过的会话再拉一次，就绪快照在新结果到来前继续可用'
        for 键 in list(自身.格子表.keys()):
            自身.刷新(键)

    def 重置会话(自身,会话标识):
        '丢掉这场会话的旧组合，再预热新目录'
        格子=自身.取格子(会话标识)
        格子.状态='cold'
        格子.命令表=()
        格子.最近错误=None
        自身.刷新(会话标识)

    def 重置已连接(自身):
        '重连后丢掉每个快照并预热'
        for 键,格子 in list(自身.格子表.items()):
            格子.状态='cold'
            格子.命令表=()
            自身.刷新(键)

    def 预热(自身,会话标识):
        '冷的或失败的会话点火拉一次'
        格子=自身.取格子(会话标识)
        if 格子.状态=='cold' or 格子.状态=='failed':
            自身.刷新(会话标识)

    def 刷新(自身,会话标识):
        '拉一次。只有仍是这场会话最新的那次才能写下 ready 或 failed'
        格子=自身.取格子(会话标识)
        格子.代次+=1
        本代=格子.代次
        if 格子.状态!='ready':
            格子.状态='pending'
        try:
            命令表=自身.拉命令(会话标识)
            if 本代!=格子.代次:
                return
            格子.命令表=tuple(命令表)
            格子.状态='ready'
            格子.最近错误=None
        except Exception as 错误:
            if 本代!=格子.代次:
                return
            格子.命令表=()
            格子.状态='failed'
            格子.最近错误=错误
        finally:
            if 本代==格子.代次:
                醒来=格子.等待者
                格子.等待者=[]
                for 唤醒 in 醒来:
                    唤醒()

    def 确保就绪(自身,会话标识,信号):
        '等到目录能用。失败或中止都抛出'
        格子=自身.取格子(会话标识)
        while True:
            if 格子.状态=='ready':
                return 格子.命令表
            if 格子.状态!='pending':
                自身.刷新(会话标识)
                if 格子.状态=='ready':
                    return 格子.命令表
                if 格子.状态=='failed':
                    raise Exception('command directory warmup failed: '+str(格子.最近错误))
                continue
            if 信号已中止(信号):
                raise 目录等待中止原因(信号)
            盒子={'错误':None}
            门=threading.Event()
            持有={}
            def 当中止(盒=持有,本盒=盒子,本门=门):
                '摘掉等待并带上中止原因'
                格子.等待者=[项 for 项 in 格子.等待者 if 项 is not 盒['完成']]
                本盒['错误']=目录等待中止原因(信号)
                本门.set()
            def 完成(盒=持有,本门=门):
                '这次拉取已经发布'
                if hasattr(信号,'removeEventListener'):
                    信号.removeEventListener('abort',盒['当中止'])
                本门.set()
            持有['完成']=完成
            持有['当中止']=当中止
            if hasattr(信号,'addEventListener'):
                信号.addEventListener('abort',当中止,{'once':True})
            格子.等待者.append(完成)
            if 格子.状态!='pending' and 完成 in 格子.等待者:
                格子.等待者=[项 for 项 in 格子.等待者 if 项 is not 完成]
                完成()
            while 门.is_set() is False:
                if 信号已中止(信号) and 盒子['错误'] is None:
                    当中止()
                    break
                门.wait(0.05)
            if 盒子['错误'] is not None:
                raise 盒子['错误']
            if 格子.状态=='failed':
                raise Exception('command directory warmup failed: '+str(格子.最近错误))

    def 取格子(自身,会话标识):
        '没有格子就建一格'
        if 会话标识 not in 自身.格子表:
            自身.格子表[会话标识]=目录格子()
        return 自身.格子表[会话标识]
