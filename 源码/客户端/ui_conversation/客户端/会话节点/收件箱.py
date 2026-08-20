"""收件箱会话节点：累计 next-turn / next-step 拼接状态。

对齐上游 `ui-conversation/src/client/conversation-nodes/inbox.ts`。公开面仅中文名。
"""
from .面辅助 import 取字段#字段

__all__=['下一回合收件箱定义','下一步收件箱定义','登记收件箱会话节点','应用拼接']#仅中文公开名

def 应用拼接(上一,拼接):#把一次拼接叠到上一状态
    """新的待处理列表与已认领集。"""
    if 上一 is not None:#有上一
        态=取字段(上一,'state') or {}#态
        待处理=list(取字段(态,'pending') or [])#待处理
        已认领=set(取字段(态,'claimed') or [])#已认领
    else:#无
        待处理=[]#空
        已认领=set()#空
    起=取字段(拼接,'start',0)#起始
    删=取字段(拼接,'removedCount',0) or 0#删除数
    插入=list(取字段(拼接,'inserted') or [])#插入
    被删=待处理[起:起+删]#被删项
    待处理[起:起+删]=插入#splice
    for 身份 in 插入:#新插入不再算已认领
        标识=取字段(身份,'id')#id
        已认领.discard(标识)#删
    if 取字段(拼接,'target')=='next-step' and 取字段(拼接,'outcome')!='canceled':#下一步且非取消
        for 身份 in 被删:#被删项记为已认领
            已认领.add(取字段(身份,'id'))#等待 user/message
    return {'pending':待处理,'claimed':已认领}#新状态

def 收件箱定义(目标):#按目标造一条纯状态定义
    """inbox-next-turn 或 inbox-next-step。"""
    种类='inbox-'+目标#kind
    def 匹配(事件):#是否本目标拼接
        """agent/inbox/spliced 且目标匹配。"""
        if 取字段(事件,'type')!='agent/inbox/spliced':#非拼接
            return None#不认领
        数据=取字段(事件,'data') or {}#载荷
        if 取字段(数据,'target')!=目标:#目标不对
            return None#不认领
        return {'id':str(取字段(事件,'seq')),'role':'start'}#以序号开
    def 开始(_上下文,匹配项,读取器):#从拼接事件开状态
        """叠到同 kind 上一状态。"""
        事件=取字段(匹配项,'event')#事件
        if 取字段(事件,'type')!='agent/inbox/spliced':#必须
            raise Exception(种类+' start requires agent/inbox/spliced')#硬失败
        上一=读取器.previous(种类) if hasattr(读取器,'previous') else None#上一
        return 应用拼接(上一,取字段(事件,'data') or {})#叠
    def 更新(上下文,_匹配项=None):#无后续 update
        """原样返回。"""
        return 取字段(上下文,'state')#态
    def 发布(_匹配项=None):#纯状态不发布视图
        """none。"""
        return 'none'#不发布
    return {'kind':种类,'match':匹配,'start':开始,'update':更新,'publication':发布}#定义

下一回合收件箱定义=收件箱定义('next-turn')#下一回合队列
下一步收件箱定义=收件箱定义('next-step')#下一步；claimed 供 message 分类

def 登记收件箱会话节点(上下文):#登记两项 Inbox 状态贡献
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(下一回合收件箱定义)#下一回合
    上下文.conversationEvents.register(下一步收件箱定义)#下一步
