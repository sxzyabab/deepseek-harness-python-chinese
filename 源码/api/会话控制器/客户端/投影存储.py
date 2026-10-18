'通用 per-session 投影值存储（推送模型；更高 seq 胜出）'
from .通知器 import 通知器#批处理通知

__all__=['投影值存储']#仅中文公开名

def _不重建():
    '通知器只批处理，不另建快照'
    return None#空

class 投影值存储:
    '一个 session 的投影值。有序号的行更高 seq 胜出；缓存行让给任何有序号的写入'

    def __init__(自身):
        '空存储'
        自身._行={}#key → {kind,value,seq?}
        自身._通道={}#key → {face,notifier}
        自身._值缓存=None#整表缓存
        自身._任意通知器=通知器(_不重建)#任意 key

    def 面(自身,键):
        '按键寻址的裸可观测面（缺席是 undefined 快照，不是缺失面）'
        return 自身._通道用于(键)['face']#面

    def 取(自身,键):
        '读某键当前整值；缺席为 None'
        行=自身._行[键] if 键 in 自身._行 else None#行
        return None if 行 is None else 行['value']#值

    def 序号于(自身,键):
        '读已接受的宿主水位。缺席和缓存行没有可比较序号'
        行=自身._行[键] if 键 in 自身._行 else None#行
        if 行 is None or 行.get('kind')!='sequenced':#无序号
            return None#缺席
        return 行['seq']#水位

    def 诸值(自身):
        '一次引用稳定的全部当前投影值'
        if 自身._值缓存 is None:#重建
            自身._值缓存=dict((键,行['value']) for 键,行 in 自身._行.items())#映射
        return 自身._值缓存#缓存

    def 订阅任意(自身,监听者):
        '订阅任意 key 变化'
        return 自身._任意通知器.订阅(监听者)#取消函数

    def 应用(自身,键,值,序号):
        '应用一条有序号的成品值。有序号的行里更高 seq 胜出，缓存行让位'
        行=自身._行[键] if 键 in 自身._行 else None#行
        if 行 is not None and 行.get('kind')=='sequenced' and 序号<=行['seq']:#陈旧
            return#丢弃
        自身._行[键]={'kind':'sequenced','value':值,'seq':序号}#写入
        自身._已变(键)#通知

    def 应用缓存(自身,值表):
        '只填还没有序号行的键。持久检查点不能压过已连接会话'
        if not isinstance(值表,dict):#无表
            return#空
        for 键 in 值表:#逐键
            行=自身._行[键] if 键 in 自身._行 else None#行
            if 行 is not None and 行.get('kind')=='sequenced':#已有序号
                continue#保留
            自身._行[键]={'kind':'cached','value':值表[键]}#缓存
            自身._已变(键)#通知

    def 播种(自身,基线):
        '用历史尾页或控制基线的 projections 块播种。先丢掉缓存行，再按序号合并'
        值表=基线['values'] if isinstance(基线.get('values'),dict) else {}#值
        切点=基线['asOfSeq']#切点
        for 键 in list(自身._行.keys()):#缓存行
            if 自身._行[键].get('kind')!='cached':#有序号
                continue#保留
            del 自身._行[键]#清除
            自身._已变(键)#通知
        for 键 in 值表:#携带键
            自身.应用(键,值表[键],切点)#应用
        for 键 in list(自身._行.keys()):#未携带键
            if 键 in 值表:#仍在
                continue#保留
            行=自身._行[键]#行
            if 行.get('kind')=='sequenced' and 行['seq']>切点:#较新帧
                continue#保留
            del 自身._行[键]#清除
            自身._已变(键)#通知

    def 清空(自身):
        '丢弃一代 Host 的值与水位，保留已订阅的面'
        for 键 in list(自身._行.keys()):#全部键
            del 自身._行[键]#删除
            自身._已变(键)#通知

    def _已变(自身,键):
        '失效缓存并通知'
        自身._值缓存=None#整表失效
        if 键 in 自身._通道:#单键
            自身._通道[键]['notifier'].标脏()#通知
        自身._任意通知器.标脏()#任意

    def _通道用于(自身,键):
        '按需创建通道'
        if 键 in 自身._通道:#已有
            return 自身._通道[键]#通道
        通知=通知器(_不重建)#无快照重建
        def 取快照():
            '读当前值'
            return 自身.取(键)#值
        通道={
            'notifier':通知,
            'face':{'getSnapshot':取快照,'subscribe':通知.订阅},
        }#通道
        自身._通道[键]=通道#缓存
        return 通道#返回
