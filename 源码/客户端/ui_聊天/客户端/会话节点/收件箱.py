from .节点工厂 import 聊天错误#本包异常

__all__=['下一回合收件箱定义','下一步收件箱定义','登记收件箱会话节点','应用拼接']#仅中文公开名

def 应用拼接(上一,拼接):#把一次拼接叠到上一状态
    """新的待处理列表与已认领集。"""
    if 上一 is not None:#有上一
        态=上一['state'] if 'state' in 上一 and 上一['state'] is not None else {}#态
        待处理=list(态['pending'] if 'pending' in 态 and 态['pending'] is not None else [])#待处理
        已认领=set(态['claimed'] if 'claimed' in 态 and 态['claimed'] is not None else [])#已认领
    else:#无
        待处理=[]#空
        已认领=set()#空
    起=拼接['start'] if 'start' in 拼接 else 0#起始
    删=拼接['removedCount'] if 'removedCount' in 拼接 and 拼接['removedCount'] is not None else 0#删除数
    插入=list(拼接['inserted'] if 'inserted' in 拼接 and 拼接['inserted'] is not None else [])#插入
    被删=待处理[起:起+删]#被删项
    待处理[起:起+删]=插入#splice
    for 身份 in 插入:#新插入不再算已认领
        标识=身份['id'] if 'id' in 身份 else None#id
        已认领.discard(标识)#删
    if ('target' in 拼接 and 拼接['target']=='next-step' and ('outcome' not in 拼接 or 拼接['outcome']!='canceled')):#下一步且非取消
        for 身份 in 被删:#被删项记为已认领
            已认领.add(身份['id'] if 'id' in 身份 else None)#等待 user/message
    return {'pending':待处理,'claimed':已认领}#新状态

def 收件箱定义(目标):#按目标造一条纯状态定义
    """inbox-next-turn 或 inbox-next-step。"""
    种类='inbox-'+目标#kind
    def 匹配(事件):#是否本目标拼接
        """agent/inbox/spliced 且目标匹配。"""
        if 事件['type']!='agent/inbox/spliced':#非拼接
            return None#不认领
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        if 'target' not in 数据 or 数据['target']!=目标:#目标不对
            return None#不认领
        return {'id':str(事件['seq']),'role':'start'}#以序号开
    def 开始(_上下文,匹配项,读取器):#从拼接事件开状态
        """叠到同 kind 上一状态。"""
        事件=匹配项['event']#事件
        if 事件['type']!='agent/inbox/spliced':#必须
            raise 聊天错误(种类+' start requires agent/inbox/spliced')#硬失败
        上一=读取器.previous(种类)#上一
        return 应用拼接(上一,事件['data'] if 'data' in 事件 else {})#叠
    def 更新(上下文,_匹配项=None):#无后续 update
        """原样返回。"""
        return 上下文['state']#态
    def 发布(_匹配项=None):#纯状态不发布视图
        """none。"""
        return 'none'#不发布
    return {'kind':种类,'match':匹配,'start':开始,'update':更新,'publication':发布}#定义

下一回合收件箱定义=收件箱定义('next-turn')#下一回合队列
下一步收件箱定义=收件箱定义('next-step')#下一步；claimed 供 message 分类

def 登记收件箱会话节点(上下文):#登记两项 Inbox 状态贡献
    """挂到 uiConversation.events。"""
    上下文.uiConversation.events.register(下一回合收件箱定义)#下一回合
    上下文.uiConversation.events.register(下一步收件箱定义)#下一步
