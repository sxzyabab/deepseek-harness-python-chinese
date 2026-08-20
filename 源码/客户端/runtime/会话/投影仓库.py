"""按会话的通用投影值仓库（推模型）。

对齐上游 `runtime/src/client/sessions/projection-store.ts`。公开面仅中文名。
宿主是唯一计算点；客户端按键持有已完成的整份值，更高 seq 胜出。
React 钩座位（useProjection）留在 web-react，本模块只落裸数据面。
"""
from .通知器 import 通知器#导入批通知器

__all__=['投影值仓库']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 空重建():#通知器空重建
    """无需重建快照缓存。"""
    return#空

class 投影值仓库:#投影值仓库
    """一个会话的投影值。基线播种与推送帧共用更高 seq 胜出规则。"""

    def __init__(自身):#空仓库
        """按键行、通道与整表缓存。"""
        自身._行们={}#键 → {value,seq}
        自身._通道们={}#键 → {face,notifier}
        自身._值缓存=None#整表快照缓存
        自身._任意通知器=通知器(空重建)#空重建：订阅者自己读行

    def 面于(自身,键):#取一键的面
        """按键的裸可观察面。

        永远有定义 — 缺席是 None 快照，从不是缺失的面。
        @param 键 - 投影键。
        @returns 该键身份稳定的面。
        """
        return 自身._通道(键)['face']#按需创建通道后返回面

    def 取(自身,键):#读一行
        """一个键的当前整份值。

        @param 键 - 投影键。
        @returns 值，键缺席时为 None。
        """
        行=自身._行们.get(键)#已有行
        if 行 is None:#没有行
            return None#缺席
        return 行['value']#完成值

    def 值们(自身):#整表快照
        """把每个当前投影值读成一份引用稳定的快照。"""
        if 自身._值缓存 is None:#缓存失效
            表={}#新表
            for 键,行 in 自身._行们.items():#只投影 value
                表[键]=行['value']#写入
            自身._值缓存=表#记下（调用方勿原地改）
        return 自身._值缓存#稳定引用

    def 订阅任意(自身,监听器):#任意键订阅
        """订阅任意键变更（微任务批）。

        @param 监听器 - 变更回调。
        @returns 取消订阅函数。
        """
        return 自身._任意通知器.订阅(监听器)#交给粗粒度通知器

    def 应用(自身,键,值,序号):#写入一行
        """应用一份完成值（session/projection 推送帧路径）。

        @param 键 - 投影键。
        @param 值 - 宿主单元算出的整份值。
        @param 序号 - 发出时单元的水位。
        """
        行=自身._行们.get(键)#已有行
        if 行 is not None and 序号<=行['seq']:#更高 seq 胜出
            return#回放与过期帧丢掉
        自身._行们[键]={'value':值,'seq':序号}#记下新行
        自身._已变(键)#作废缓存并通知

    def 播种(自身,基线):#播种基线
        """从历史尾页的 projections 块播种。

        @param 基线 - 响应里的 projections 块（asOfSeq + values）。
        """
        值表=取字段(基线,'values') or {}#开放键空间
        切面=取字段(基线,'asOfSeq')#切面序号
        for 键 in list(值表.keys() if isinstance(值表,dict) else []):#携带的键
            自身.应用(键,值表[键],切面)#按切面 seq 写入
        for 键 in list(自身._行们.keys()):#检查仓库已有键
            if isinstance(值表,dict) and 键 in 值表:#基线仍携带则留下
                continue#留下
            行=自身._行们[键]#当前行
            if 行['seq']>切面:#更新的帧已超过切面则不清
                continue#留下
            del 自身._行们[键]#切面缺席且无更新帧：能力缺席
            自身._已变(键)#通知

    def 截断(自身,末序号):#截到持久基线
        """丢掉超过复用世代基线的行。

        @param 末序号 - subscribed 帧的持久基线 seq。
        """
        for 键 in list(自身._行们.keys()):#逐行
            行=自身._行们[键]#当前
            if 行['seq']<=末序号:#仍在基线内则留下
                continue#留下
            del 自身._行们[键]#丢掉重启不可信的行
            自身._已变(键)#通知

    def _已变(自身,键):#一行变了
        """作废缓存并通知该键与任意键通道。"""
        自身._值缓存=None#整表缓存作废
        通道=自身._通道们.get(键)#该键通道
        if 通道 is not None:#有
            通道['notifier'].标脏()#该键微任务批
        自身._任意通知器.标脏()#任意键微任务批

    def _通道(自身,键):#按需取通道
        """第一次见到该键时创建身份稳定的面。"""
        通道=自身._通道们.get(键)#已有
        if 通道 is not None:#有
            return 通道#返回
        通知=通知器(空重建)#空重建
        仓库=自身#闭包读行
        def 取快照():#直接读行
            """该键当前值。"""
            行=仓库._行们.get(键)#行
            if 行 is None:#无
                return None#缺席
            return 行['value']#值
        通道={#新通道
            'notifier':通知,#批通知
            'face':{'getSnapshot':取快照,'subscribe':通知.订阅},#裸面
        }#结束
        自身._通道们[键]=通道#缓存
        return 通道#新建
