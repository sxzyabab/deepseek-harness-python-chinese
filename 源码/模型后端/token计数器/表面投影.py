"""token-meter 投影单元共用的 O(1) 表面 token 折叠。对齐上游 `token-meter/src/surface-projection.ts`。公开面仅中文名。"""
from ...内核.会话 import 事件派生消息,是否表面事件#消息导出与表面判定
from .类型 import 计量错误#计量异常
from .计价 import 计价消息#消息计价

__all__=['折叠表面投影']#仅中文公开名

def 折叠表面投影(声明,事件):#把一条已提交事件折到运行中的表面合计上
    """把一条已提交事件折到运行中的表面 token 合计上。事件与声明均为 dict。"""
    种类=事件['type']#事件类型
    if 种类=='compaction/summary' or 种类=='compaction/prune':#影子价格事件
        数据=事件['data']#载荷
        范围=数据['shadowedRange']#被遮蔽范围
        return {'deltaTokens':0,'claim':{'start':范围['start'],'end':范围['end'],'tokens':数据['shadowedTokenCount']}}#武装声明，合计不变
    if not 是否表面事件(事件):#非表面则过期声明
        return {'deltaTokens':0,'claim':None}#过期声明
    消息=事件派生消息(事件)#导出消息
    令牌数=0 if 消息 is None else 计价消息(消息)#无消息则0
    操作=事件['surfaceOp']#表面操作
    if 操作=='append':#追加并过期声明
        return {'deltaTokens':令牌数,'claim':None}#追加
    if 声明 is None:#无声明则零增量
        return {'deltaTokens':0,'claim':None}#历史回放退化成漂移
    起点=操作['startSeq']#替换起点
    终点=操作['endSeq']#替换终点
    if 声明['start']!=起点 or 声明['end']!=终点:#声明范围对不上
        raise 计量错误(
            'token surface: replace at seq '+str(事件['seq'])+' over range '+str(起点)+'-'+str(终点)+' has no adjacent shadow price'
            +' (armed claim covers '+str(声明['start'])+'-'+str(声明['end'])+')'
        )#相邻影子价格违约
    return {'deltaTokens':令牌数-声明['tokens'],'claim':None}#新价格减去被遮蔽
