"""通用 per-session 投影值存储（推送模型；更高 seq 胜出）。

对齐上游 `session-controller/src/client/sessions/projection-store.ts`。公开面仅中文名。
React `useProjection` 钩子面跳过（纯 React）；本模块交付存储与按键可观察面。
"""
from .通知器 import 通知器#批处理通知

__all__=['投影值存储']#仅中文公开名

class 投影值存储:
    """一个 session 的投影值。基线播种；推送帧更新；较低或相等 seq 均输。"""

    def __init__(自身):
        """空存储。"""
        自身._行={}#key → {value,seq}
        自身._通道={}#key → {face,notifier}
        自身._值缓存=None#整表缓存
        自身._任意通知器=通知器(lambda:None)#任意 key

    def 面(自身,键):
        """按键寻址的裸可观测面（缺席是 undefined 快照，不是缺失面）。"""
        return 自身._通道用于(键)['face']#面

    def 取(自身,键):
        """读某键当前整值；缺席为 None。"""
        行=自身._行[键] if 键 in 自身._行 else None#行
        return None if 行 is None else 行['value']#值

    def 诸值(自身):
        """一次引用稳定的全部当前投影值。"""
        if 自身._值缓存 is None:#重建
            自身._值缓存=dict((键,行['value']) for 键,行 in 自身._行.items())#映射
        return 自身._值缓存#缓存

    def 订阅任意(自身,监听者):
        """订阅任意 key 变化。"""
        return 自身._任意通知器.订阅(监听者)#取消函数

    def 应用(自身,键,值,序号):
        """应用控制流一条成品值；更高 seq 胜出。"""
        行=自身._行[键] if 键 in 自身._行 else None#行
        if 行 is not None and 序号<=行['seq']:#陈旧
            return#丢弃
        自身._行[键]={'value':值,'seq':序号}#写入
        自身._已变(键)#通知

    def 播种(自身,基线):
        """用历史尾页 projections 块播种。基线含 asOfSeq／values。"""
        值表=基线['values'] if isinstance(基线.get('values'),dict) else {}#值
        切点=基线['asOfSeq']#切点
        for 键 in 值表:#携带键
            自身.应用(键,值表[键],切点)#应用
        for 键 in list(自身._行.keys()):#未携带键
            if 键 in 值表:#仍在
                continue#保留
            if 自身._行[键]['seq']>切点:#较新帧
                continue#保留
            del 自身._行[键]#清除
            自身._已变(键)#通知

    def 截断(自身,末序号):
        """丢弃超出替换控制基线的行。"""
        for 键 in list(自身._行.keys()):#扫描
            if 自身._行[键]['seq']<=末序号:#保留
                continue#下一项
            del 自身._行[键]#删除
            自身._已变(键)#通知

    def _已变(自身,键):
        """失效缓存并通知。"""
        自身._值缓存=None#整表失效
        if 键 in 自身._通道:#单键
            自身._通道[键]['notifier'].标脏()#通知
        自身._任意通知器.标脏()#任意

    def _通道用于(自身,键):
        """按需创建通道。"""
        if 键 in 自身._通道:#已有
            return 自身._通道[键]#通道
        通知=通知器(lambda:None)#无快照重建
        def 取快照():
            """读当前值。"""
            return 自身.取(键)#值
        通道={
            'notifier':通知,
            'face':{'getSnapshot':取快照,'subscribe':通知.订阅},
        }#通道
        自身._通道[键]=通道#缓存
        return 通道#返回
